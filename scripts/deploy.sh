#!/usr/bin/env bash
# deploy.sh — One-command deployment for pip-bot on Raspberry Pi
#
# This script pulls the latest code from main, installs dependencies,
# and restarts the bot service via systemd.
#
# Usage:
#   From Raspberry Pi (direct): bash scripts/deploy.sh
#   From PC (via SSH): ssh pi@<rpi-ip> "cd ~/pip-bot && bash scripts/deploy.sh"
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

# Colors for output (works on both terminals and CI)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Verify prerequisites
verify_setup() {
    log_info "Verifying deployment prerequisites..."
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        echo "Please clone pip-bot to $PROJECT_DIR first"
        exit 1
    fi
    
    if [ ! -f "$POETRY_BIN" ]; then
        log_error "Poetry not found at: $POETRY_BIN"
        echo "Please install Poetry: pip3 install poetry --user"
        exit 1
    fi
    
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl not found. Are you running on Raspberry Pi OS?"
        exit 1
    fi
    
    log_info "Prerequisites verified"
}

# Pull latest code from GitHub
pull_code() {
    log_info "Pulling latest code from origin/main..."
    cd "$PROJECT_DIR"
    
    # Backup .env before git reset in case it's accidentally committed
    if [ -f ".env" ]; then
        log_info "Backing up .env before pulling code..."
        cp .env .env.backup.pre-deploy
    fi
    
    if ! git fetch origin main &> /dev/null; then
        log_error "Failed to fetch from GitHub. Check your internet connection."
        exit 1
    fi
    
    if ! git checkout main &> /dev/null; then
        log_error "Failed to checkout main branch"
        exit 1
    fi
    
    # Warn about any other modified or untracked files that will be lost.
    # We exclude .env because it is already backed up above.
    dirty=$(git status --porcelain | grep -v "^.. \.env")
    if [ -n "$dirty" ]; then
        log_warn "The following files will be discarded by git reset:"
        echo "$dirty"
        log_warn "Back them up now if needed (Ctrl-C to abort)."
    fi

    if ! git reset --hard origin/main &> /dev/null; then
        log_error "Failed to reset to origin/main"
        exit 1
    fi
    
    # Restore .env if it was backed up
    if [ -f ".env.backup.pre-deploy" ]; then
        log_info "Restoring .env from backup..."
        cp .env.backup.pre-deploy .env
        rm .env.backup.pre-deploy
    fi
    
    log_info "Code pulled successfully"
}

# Install dependencies using Poetry
install_dependencies() {
    log_info "Installing dependencies with Poetry..."
    cd "$PROJECT_DIR"
    
    POETRY_BIN="${HOME}/.local/bin/poetry"
    
    # Remove stale lock file so Poetry regenerates it from pyproject.toml
    rm -f "$PROJECT_DIR/poetry.lock"

    # Try the standard location first
    if [ -f "$POETRY_BIN" ]; then
        if ! output=$($POETRY_BIN lock 2>&1); then
            log_error "Poetry lock failed with output: $output"
            exit 1
        fi
        if ! output=$($POETRY_BIN install --only main 2>&1); then
            log_error "Poetry install failed with output: $output"
            exit 1
        fi
    # Fall back to poetry in PATH
    elif command -v poetry &> /dev/null; then
        if ! output=$(poetry lock 2>&1); then
            log_error "Poetry lock failed with output: $output"
            exit 1
        fi
        if ! output=$(poetry install --only main 2>&1); then
            log_error "Poetry install failed with output: $output"
            exit 1
        fi
    else
        log_error "Poetry not found at: $POETRY_BIN"
        echo "Please install Poetry: pip3 install poetry --user"
        exit 1
    fi
    
    log_info "Dependencies installed successfully"
}

# Restart systemd service
restart_service() {
    log_info "Restarting $SERVICE_NAME service..."
    
    if ! sudo systemctl restart $SERVICE_NAME 2> /dev/null; then
        log_error "Failed to restart service. Check systemctl status:"
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
    
    # Wait a moment for service to restart
    sleep 2
    
    # Verify service is running
    if ! sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_error "Service failed to start. Check logs with: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
    
    log_info "Service restarted successfully"
}

# Summary
print_summary() {
    log_info "Deployment completed successfully!"
    echo ""
    echo "Summary:"
    echo "  • Code pulled from origin/main"
    echo "  • Dependencies installed"
    echo "  • Service restarted (running as 'pi' user)"
    echo ""
    echo "Next steps:"
    echo "  • Check bot status: journalctl -u $SERVICE_NAME -f"
    echo "  • View logs: journalctl -u $SERVICE_NAME --since today"
    echo ""
}

# Main deployment flow
main() {
    echo ""
    log_info "Starting pip-bot deployment..."
    echo ""
    
    verify_setup
    pull_code
    install_dependencies
    restart_service
    print_summary
}

# Run main function
main
