#!/usr/bin/env bash
# deploy_branch.sh — Deploy a specific branch to the Raspberry Pi for testing
#
# Use this script to validate a feature branch on the Pi before merging to main.
# When done testing, run scripts/deploy.sh to return to main.
#
# Usage:
#   From Raspberry Pi (direct):
#     bash scripts/deploy_branch.sh <branch>
#
#   From PC (via SSH):
#     ssh pi@<rpi-ip> "cd ~/pip-bot && bash scripts/deploy_branch.sh <branch>"
#
#   From PC (push branch then deploy remotely):
#     git push origin <branch> && ssh pi@<rpi-ip> "cd ~/pip-bot && bash scripts/deploy_branch.sh <branch>"
#
# Prerequisites:
#   - Running on Raspberry Pi with pip-bot cloned to /home/pi/pip-bot
#   - Poetry installed at /home/pi/.local/bin/poetry
#   - systemd service "pip-bot" enabled and running
#   - sudo access available (for systemctl commands)
#
# Exit codes:
#   0 — Deployment successful
#   1 — Error during deployment (check output for details)

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# Configuration
PROJECT_DIR="${HOME}/pip-bot"
POETRY_BIN="${HOME}/.local/bin/poetry"
SERVICE_NAME="pip-bot"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Validate branch argument
validate_args() {
    if [ -z "${BRANCH}" ]; then
        log_error "Branch name is required."
        echo ""
        echo "Usage: bash scripts/deploy_branch.sh <branch>"
        echo "Example: bash scripts/deploy_branch.sh fix/audit-findings"
        exit 1
    fi
}

# Verify prerequisites
verify_setup() {
    log_step "Verifying deployment prerequisites..."

    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        echo "Please clone pip-bot to $PROJECT_DIR first"
        exit 1
    fi

    if [ ! -f "$POETRY_BIN" ] && ! command -v poetry &> /dev/null; then
        log_error "Poetry not found. Please install: pip3 install poetry --user"
        exit 1
    fi

    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. Are you running on Raspberry Pi OS?"
        exit 1
    fi

    log_info "Prerequisites verified"
}

# Checkout the requested branch
checkout_branch() {
    log_step "Fetching and checking out branch '${BRANCH}'..."
    cd "$PROJECT_DIR"

    # Fetch all branches from origin (show errors, suppress progress noise)
    log_info "Fetching from origin..."
    if ! git fetch --no-progress origin 2>&1; then
        log_error "Failed to fetch from GitHub. Check your internet connection."
        exit 1
    fi

    # Verify the branch exists on origin
    if ! git ls-remote --exit-code --heads origin "${BRANCH}" > /dev/null 2>&1; then
        log_error "Branch '${BRANCH}' not found on origin."
        echo "Make sure you have pushed the branch: git push origin ${BRANCH}"
        exit 1
    fi

    # Backup .env before resetting
    if [ -f ".env" ]; then
        log_info "Backing up .env..."
        cp .env .env.backup.pre-deploy
    fi

    # Warn about local changes that will be discarded
    dirty=$(git status --porcelain | grep -v "^.. \.env" || true)
    if [ -n "$dirty" ]; then
        log_warn "The following local changes will be discarded:"
        echo "$dirty"
        log_warn "Back them up now if needed (Ctrl-C to abort)."
        sleep 3
    fi

    # Switch to the target branch and reset to origin
    log_info "Checking out '${BRANCH}'..."
    if ! git checkout -q "${BRANCH}"; then
        log_error "Failed to checkout branch '${BRANCH}'"
        exit 1
    fi

    log_info "Resetting to origin/${BRANCH}..."
    if ! git reset --hard "origin/${BRANCH}"; then
        log_error "Failed to reset to origin/${BRANCH}"
        exit 1
    fi

    # Restore .env
    if [ -f ".env.backup.pre-deploy" ]; then
        log_info "Restoring .env from backup..."
        cp .env.backup.pre-deploy .env
        rm .env.backup.pre-deploy
    fi

    DEPLOYED_COMMIT=$(git rev-parse --short HEAD)
    log_info "Checked out '${BRANCH}' at ${DEPLOYED_COMMIT}"
}

# Install dependencies using Poetry
install_dependencies() {
    log_step "Installing dependencies with Poetry..."
    cd "$PROJECT_DIR"

    POETRY_CMD="$POETRY_BIN"
    if [ ! -f "$POETRY_BIN" ]; then
        POETRY_CMD="poetry"
    fi

    if ! output=$($POETRY_CMD install --only main --no-interaction 2>&1); then
        log_error "Poetry install failed: $output"
        exit 1
    fi

    log_info "Dependencies installed successfully"
}

# Restart systemd service
restart_service() {
    log_step "Restarting $SERVICE_NAME service..."

    if ! sudo systemctl restart $SERVICE_NAME 2> /dev/null; then
        log_error "Failed to restart service."
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi

    sleep 2

    if ! sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_error "Service failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi

    log_info "Service restarted successfully"
}

# Summary
print_summary() {
    echo ""
    log_info "Branch deployment completed!"
    echo ""
    echo -e "  Branch:  ${CYAN}${BRANCH}${NC} (${DEPLOYED_COMMIT})"
    echo "  Service: ${SERVICE_NAME} is running"
    echo ""
    echo "Useful commands:"
    echo "  Watch logs:  journalctl -u ${SERVICE_NAME} -f"
    echo "  View errors: journalctl -u ${SERVICE_NAME} -p err --since today"
    echo ""
    echo -e "${YELLOW}When done testing, return to main:${NC}"
    echo "  bash scripts/deploy.sh"
    echo ""
}

# Main
BRANCH="${1}"

main() {
    echo ""
    log_warn "BRANCH DEPLOYMENT — not a production deploy"
    echo ""

    validate_args
    verify_setup
    checkout_branch
    install_dependencies
    restart_service
    print_summary
}

main
