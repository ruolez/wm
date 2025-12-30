#!/bin/bash
# =============================================================================
# Warehouse Management - Production Installer
# Target: Ubuntu 22.04/24.04 LTS
# =============================================================================
#
# This script performs a complete installation of the Warehouse Management
# application including:
# - Docker and Docker Compose installation
# - SQL Server 2022 Express container
# - Application services (api1, api_admin, nginx)
# - Automatic CORS configuration based on detected IP
# - Database schema initialization
#
# Usage: sudo ./install.sh [options]
#
# Options:
#   --ip <address>    Specify IP address instead of auto-detect
#   --uninstall       Remove all containers and data
#   --update          Rebuild and restart with local files
#   --update-github   Pull latest from GitHub, rebuild and restart
#   --help            Show this help message
#
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  Warehouse Management - Installer"
    echo "=============================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (sudo)"
        echo "Usage: sudo $0"
        exit 1
    fi
}

show_help() {
    echo "Usage: sudo $0 [options]"
    echo ""
    echo "Options:"
    echo "  --ip <address>    Specify IP address instead of auto-detect"
    echo "  --uninstall       Remove all containers and data"
    echo "  --update          Rebuild and restart with local files"
    echo "  --update-github   Pull latest from GitHub, rebuild and restart"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0                     # Fresh install with auto-detected IP"
    echo "  sudo $0 --ip 192.168.1.100  # Install with specific IP"
    echo "  sudo $0 --update            # Update with local changes"
    echo "  sudo $0 --update-github     # Update from GitHub repository"
    echo "  sudo $0 --uninstall         # Remove installation"
    exit 0
}

# =============================================================================
# Installation Functions
# =============================================================================

detect_ip() {
    # Try to detect the primary IP address
    local detected_ip=$(hostname -I 2>/dev/null | awk '{print $1}')

    if [ -z "$detected_ip" ]; then
        detected_ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' | head -1)
    fi

    if [ -z "$detected_ip" ]; then
        detected_ip="127.0.0.1"
    fi

    echo "$detected_ip"
}

install_docker() {
    if command -v docker &> /dev/null; then
        print_info "Docker is already installed"
        docker --version
        return 0
    fi

    print_info "Installing Docker..."

    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Install prerequisites
    apt-get update
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Set up repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    print_success "Docker installed successfully"
    docker --version
}

generate_secrets() {
    # Generate random secrets
    SA_PASSWORD="WH_$(openssl rand -hex 8)!"
    SECRET=$(openssl rand -hex 32)
    SECRET1=$(openssl rand -hex 32)
    X_TOKEN=$(openssl rand -hex 16)
}

create_env_file() {
    local host_ip="$1"

    print_info "Creating .env configuration file..."

    cat > .env << EOF
# Warehouse Management - Environment Configuration
# Generated by install.sh on $(date)

# Database Configuration
DATABASE_URL1=mssql+pyodbc://sa:${SA_PASSWORD}@sqlserver:1433/DB_admin?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=Yes&Encrypt=no&MARS_Connection=Yes
SA_PASSWORD=${SA_PASSWORD}

# Network Configuration
HOST_IP=${host_ip}
sr=${host_ip}
pr=${host_ip}

# CORS Configuration
CORS_ORIGINS=http://${host_ip},http://localhost,http://127.0.0.1

# Security
SECRET=${SECRET}
SECRET1=${SECRET1}
X_TOKEN=${X_TOKEN}

# Application Mode
MODE=PROD
SCW_INDEX=4

# Session Configuration
MAX_SESSIONS_PER_USER=3
HARD_EXPIRATION_HOURS=36

# SMTP Configuration (configure later via admin panel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=
SMTP_SENDER_EMAIL=
SMTP_PASSWORD=

# Misc
EXPIRED_DAYS=1
EXPIRED_MINUTES=1
EOF

    chmod 600 .env
    print_success ".env file created"
}

build_images() {
    print_info "Building Docker images..."

    # Build base image first
    print_info "Building base image..."
    docker build -f Dockerfile.base -t base .

    # Build all services
    print_info "Building application services..."
    docker compose build

    print_success "Docker images built successfully"
}

start_containers() {
    print_info "Starting containers..."
    docker compose up -d
    print_success "Containers started"
}

wait_for_sqlserver() {
    print_info "Waiting for SQL Server to be ready..."

    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "${SA_PASSWORD}" -C -Q "SELECT 1" &>/dev/null; then
            print_success "SQL Server is ready"
            return 0
        fi

        echo -ne "\r  Waiting... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo ""
    print_error "SQL Server failed to start within timeout"
    return 1
}

initialize_database() {
    print_info "Initializing database schema..."

    # Copy init script to container and execute
    docker cp init-db/init.sql sqlserver:/tmp/init.sql

    docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
        -S localhost \
        -U sa \
        -P "${SA_PASSWORD}" \
        -C \
        -i /tmp/init.sql

    print_success "Database initialized successfully"
}

restart_services() {
    print_info "Restarting application services..."
    docker compose restart api1 api_admin
    sleep 5
    print_success "Services restarted"
}

# =============================================================================
# Uninstall Function
# =============================================================================

uninstall() {
    print_warning "This will remove all containers and data!"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Uninstall cancelled"
        exit 0
    fi

    print_info "Stopping and removing containers..."
    docker compose down -v 2>/dev/null || true

    print_info "Removing Docker images..."
    docker rmi base api1 api_admin nginx 2>/dev/null || true

    print_info "Removing .env file..."
    rm -f .env

    print_success "Uninstall complete"
    exit 0
}

# =============================================================================
# Update Function
# =============================================================================

update() {
    if [ ! -f .env ]; then
        print_error "No existing installation found. Run install first."
        exit 1
    fi

    print_info "Updating existing installation..."

    # Rebuild and restart with local files
    build_images
    docker compose up -d

    print_success "Update complete"
    exit 0
}

# =============================================================================
# Update from GitHub Function
# =============================================================================

update_github() {
    print_info "Updating from GitHub..."

    # Check if we're in a git repository
    if [ ! -d .git ]; then
        print_error "Not a git repository. Cannot update from GitHub."
        print_info "If this is a fresh installation, clone the repository first:"
        print_info "  git clone https://github.com/ruolez/wm.git"
        exit 1
    fi

    # Check for .env file
    if [ ! -f .env ]; then
        print_error "No existing installation found. Run install first."
        exit 1
    fi

    # Stash any local changes to prevent conflicts
    print_info "Stashing local changes..."
    git stash --include-untracked 2>/dev/null || true

    # Pull latest from GitHub
    print_info "Pulling latest changes from GitHub..."
    if ! git pull origin main; then
        print_error "Git pull failed. Please resolve conflicts manually."
        git stash pop 2>/dev/null || true
        exit 1
    fi

    # Restore local changes (like .env)
    git stash pop 2>/dev/null || true

    # Rebuild and restart
    print_info "Rebuilding images with latest code..."
    build_images
    docker compose up -d

    print_success "Update from GitHub complete"
    exit 0
}

# =============================================================================
# Main Installation
# =============================================================================

main_install() {
    local host_ip="$1"

    print_header

    # Step 1: Check requirements
    print_info "Checking requirements..."
    check_root

    # Step 2: Confirm IP address
    echo -e "${YELLOW}Detected IP address: ${host_ip}${NC}"
    read -p "Use this IP for CORS configuration? [Y/n]: " confirm
    if [[ $confirm == [nN] ]]; then
        read -p "Enter IP address: " host_ip
    fi

    # Step 3: Install Docker
    install_docker

    # Step 4: Generate secrets
    generate_secrets

    # Step 5: Create .env file
    create_env_file "$host_ip"

    # Step 6: Build images
    build_images

    # Step 7: Start containers
    start_containers

    # Step 8: Wait for SQL Server
    wait_for_sqlserver

    # Step 9: Initialize database
    initialize_database

    # Step 10: Restart services (to pick up database)
    restart_services

    # Final success message
    echo ""
    echo -e "${GREEN}"
    echo "=============================================="
    echo "  Installation Complete!"
    echo "=============================================="
    echo -e "${NC}"
    echo ""
    echo "  Access the application:"
    echo "  ----------------------------------------"
    echo "  Main App:     http://${host_ip}"
    echo "  Admin Panel:  http://${host_ip}/admin"
    echo ""
    echo "  Default Login:"
    echo "  ----------------------------------------"
    echo "  Username: admin"
    echo "  Password: admin"
    echo ""
    echo "  SQL Server:"
    echo "  ----------------------------------------"
    echo "  Host: localhost:1433"
    echo "  User: sa"
    echo "  Pass: ${SA_PASSWORD}"
    echo ""
    echo -e "${YELLOW}  IMPORTANT: Change default passwords!${NC}"
    echo ""
    echo "  Useful Commands:"
    echo "  ----------------------------------------"
    echo "  View logs:    docker compose logs -f"
    echo "  Restart:      docker compose restart"
    echo "  Stop:         docker compose down"
    echo "  Update:       sudo ./install.sh --update"
    echo ""
    echo "=============================================="
}

# =============================================================================
# Parse Arguments
# =============================================================================

HOST_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --ip)
            HOST_IP="$2"
            shift 2
            ;;
        --uninstall)
            check_root
            uninstall
            ;;
        --update)
            check_root
            update
            ;;
        --update-github)
            check_root
            update_github
            ;;
        --help|-h)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Auto-detect IP if not specified
if [ -z "$HOST_IP" ]; then
    HOST_IP=$(detect_ip)
fi

# Run main installation
main_install "$HOST_IP"
