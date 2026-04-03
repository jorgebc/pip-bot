#!/usr/bin/env bash
# setup_rpi.sh — First-time setup on a fresh Raspberry Pi
#
# This script automates the initial configuration of pip-bot on a Raspberry Pi:
#   1. Clones the repository from GitHub
#   2. Installs Poetry
#   3. Installs Python dependencies
#   4. Creates .env file from template
#   5. Installs systemd service
#   6. Enables and starts the service
#
# Usage:
#   cd /home/pi
#   curl -sSL https://raw.githubusercontent.com/<owner>/pip-bot/main/scripts/setup_rpi.sh | bash
#   OR
#   bash setup_rpi.sh
#
# Prerequisites:
#   - Fresh Raspberry Pi OS (Debian 12 Bookworm) installation
#   - Sudo access available
#   - Internet connectivity for GitHub and package downloads
#   - ~1GB free disk space
#
# After running:
#   1. Edit /home/pi/pip-bot/.env with your DISCORD_TOKEN and other secrets
#   2. Run: sudo systemctl start pip-bot
#   3. Check status: journalctl -u pip-bot -f
#
# Exit codes:
#   0 — Setup successful
#   1 — Error during setup (check output for details)

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Configuration
REPO_URL="${REPO_URL:-https://github.com/jorgebc/pip-bot.git}"
INSTALL_DIR="${HOME}/pip-bot"
PROJECT_USER="$(whoami)"

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

log_section() {
    echo ""
    echo -e "${BLUE}━━━ $1 ━━━${NC}"
}

# Check if running as root (not recommended but allowed for install commands)
check_user() {
    if [ "$EUID" -eq 0 ]; then
        log_warn "Running as root. Some commands will not execute correctly."
        log_warn "It's recommended to run this script as 'pi' user."
    fi
}

# Verify prerequisites
verify_prerequisites() {
    log_section "Verifying Prerequisites"
    
    if [ ! -f /etc/os-release ]; then
        log_error "Cannot determine OS type. Is this Raspberry Pi OS?"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "git is not installed. Please run: sudo apt install git"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please run: sudo apt install python3"
        exit 1
    fi
    
    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Directory $INSTALL_DIR already exists"
        read -p "Do you want to continue and potentially overwrite it? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled"
            exit 0
        fi
    fi
    
    log_info "Prerequisites verified"
}

# Clone repository
clone_repository() {
    log_section "Cloning Repository"
    
    if [ -d "$INSTALL_DIR" ]; then
        log_info "Directory exists, updating repository..."
        cd "$INSTALL_DIR"
        git fetch origin main &> /dev/null || true
        git reset --hard origin/main &> /dev/null || true
    else
        log_info "Cloning from $REPO_URL..."
        if ! git clone "$REPO_URL" "$INSTALL_DIR" &> /dev/null; then
            log_error "Failed to clone repository"
            exit 1
        fi
    fi
    
    cd "$INSTALL_DIR"
    log_info "Repository ready at $INSTALL_DIR"
}

# Install Poetry
install_poetry() {
    log_section "Installing Poetry"
    
    POETRY_BIN="${HOME}/.local/bin/poetry"
    
    # Check if Poetry is already installed in expected location
    if [ -f "$POETRY_BIN" ]; then
        log_info "Poetry already installed at: $POETRY_BIN"
        return 0
    fi
    
    # Check if Poetry is in PATH
    if command -v poetry &> /dev/null; then
        log_info "Poetry already installed: $(command -v poetry)"
        return 0
    fi
    
    log_info "Installing Poetry for user $PROJECT_USER..."
    
    # Use pip3 to install Poetry in user directory
    if ! python3 -m pip install --user poetry --quiet 2>/dev/null; then
        log_error "Failed to install Poetry with pip3"
        log_error "Try manually: python3 -m pip install --user poetry"
        exit 1
    fi
    
    # Verify installation
    if [ ! -f "$POETRY_BIN" ]; then
        log_error "Poetry binary not found at $POETRY_BIN after installation"
        log_error "Poetry may have been installed to a different location"
        log_error "Run: python3 -m poetry --version to verify installation"
        exit 1
    fi
    
    log_info "Poetry installed successfully at $POETRY_BIN"
}

# Install Python dependencies
install_dependencies() {
    log_section "Installing Python Dependencies"
    
    cd "$INSTALL_DIR"
    POETRY_BIN="${HOME}/.local/bin/poetry"
    
    log_info "Installing dependencies with Poetry (this may take a few minutes)..."
    
    # Try to run Poetry from the installed location first
    if [ -f "$POETRY_BIN" ]; then
        if ! $POETRY_BIN install --no-dev 2>&1 | grep -v "^$" > /dev/null; then
            log_error "Failed to install dependencies with Poetry"
            log_error "Try running manually: cd $INSTALL_DIR && $POETRY_BIN install --no-dev"
            exit 1
        fi
    # Fall back to poetry in PATH
    elif command -v poetry &> /dev/null; then
        if ! poetry install --no-dev 2>&1 | grep -v "^$" > /dev/null; then
            log_error "Failed to install dependencies with Poetry"
            log_error "Try running manually: cd $INSTALL_DIR && poetry install --no-dev"
            exit 1
        fi
    else
        log_error "Poetry not found at $POETRY_BIN or in PATH"
        log_error "Please install Poetry: python3 -m pip install --user poetry"
        exit 1
    fi
    
    log_info "Dependencies installed successfully"
}

# Create environment configuration
create_env() {
    log_section "Creating Environment Configuration"
    
    cd "$INSTALL_DIR"
    
    if [ -f ".env" ]; then
        log_warn ".env already exists"
        return 0
    fi
    
    if [ ! -f ".env.example" ]; then
        log_error ".env.example not found in $INSTALL_DIR"
        exit 1
    fi
    
    log_info "Copying .env.example to .env..."
    cp .env.example .env
    
    log_warn "⚠️  IMPORTANT: Edit .env file with your Discord credentials"
    log_info "File location: $INSTALL_DIR/.env"
    echo ""
    echo "Required configuration:"
    echo "  • DISCORD_TOKEN — your Discord bot token"
    echo "  • DISCORD_GUILD_ID — your Discord server ID"
    echo ""
}

# Install systemd service
install_systemd_service() {
    log_section "Installing Systemd Service"
    
    cd "$INSTALL_DIR"
    
    if [ ! -f "pip-bot.service" ]; then
        log_error "pip-bot.service not found in $INSTALL_DIR"
        exit 1
    fi
    
    log_info "Copying service file to /etc/systemd/system/..."
    
    if ! sudo cp pip-bot.service /etc/systemd/system/ 2> /dev/null; then
        log_error "Failed to copy service file (sudo required)"
        exit 1
    fi
    
    log_info "Reloading systemd daemon..."
    if ! sudo systemctl daemon-reload 2> /dev/null; then
        log_error "Failed to reload systemd daemon"
        exit 1
    fi
    
    log_info "Systemd service installed successfully"
}

# Enable service
enable_service() {
    log_section "Enabling Systemd Service"

    log_info "Enabling pip-bot to start on boot..."

    if ! sudo systemctl enable pip-bot 2> /dev/null; then
        log_error "Failed to enable service"
        exit 1
    fi

    log_info "Service enabled (will start automatically on reboot)"
}

# Validate that the bot can run 'sudo reboot' without a password prompt.
# The /reboot command requires a passwordless sudoers entry for the pi user.
check_reboot_sudoers() {
    log_section "Checking Sudoers Entry for Reboot"

    # sudo -l -n lists allowed commands without prompting for a password.
    # We grep for a NOPASSWD rule that covers the reboot binary.
    if sudo -l -n 2>/dev/null | grep -q "NOPASSWD.*reboot"; then
        log_info "Sudoers entry for reboot is configured correctly"
        return 0
    fi

    log_warn "No passwordless sudo rule found for 'reboot'."
    echo ""
    echo "  The /reboot Discord command runs 'sudo reboot' as the service user."
    echo "  Without a sudoers entry the command will fail at runtime."
    echo ""
    echo "  To fix, run:  sudo visudo -f /etc/sudoers.d/pip-bot"
    echo "  And add the following line:"
    echo "    ${PROJECT_USER} ALL=(ALL) NOPASSWD: /sbin/reboot"
    echo ""
    log_warn "Setup will continue, but /reboot will not work until sudoers is updated."
}

# Final summary
print_summary() {
    log_section "Setup Complete!"
    
    echo ""
    echo "✓ pip-bot is now installed on your Raspberry Pi"
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║ REQUIRED: Configure Discord credentials before starting    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Edit your Discord configuration:"
    echo "  nano $INSTALL_DIR/.env"
    echo ""
    echo "Required fields:"
    echo "  • DISCORD_TOKEN — bot token from Discord Developer Portal"
    echo "  • DISCORD_GUILD_ID — your Discord server ID"
    echo ""
    echo "After editing .env:"
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║ Starting the bot                                           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  1. Start the service:"
    echo "     sudo systemctl start pip-bot"
    echo ""
    echo "  2. Check the logs (live):"
    echo "     journalctl -u pip-bot -f"
    echo ""
    echo "  3. Check service status:"
    echo "     sudo systemctl status pip-bot"
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║ Future updates                                             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  When you push code to GitHub, deploy with:"
    echo "    bash $INSTALL_DIR/scripts/deploy.sh"
    echo ""
    echo "Documentation: https://github.com/jorgebc/pip-bot#readme"
    echo ""
}

# Main setup flow
main() {
    echo ""
    log_info "Starting pip-bot setup on Raspberry Pi..."
    echo ""
    
    check_user
    verify_prerequisites
    clone_repository
    install_poetry
    install_dependencies
    create_env
    install_systemd_service
    enable_service
    check_reboot_sudoers
    print_summary
}

# Run main function
main