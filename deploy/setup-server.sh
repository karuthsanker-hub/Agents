#!/bin/bash
# =============================================================================
# AWS EC2 Server Setup Script for Arctic Debate Card Agent
# Author: Shiv Sanker
# 
# Usage: 
#   1. SSH into your EC2 instance
#   2. Run: curl -sSL https://raw.githubusercontent.com/YOUR_REPO/main/deploy/setup-server.sh | bash
#   OR
#   1. Copy this file to server
#   2. chmod +x setup-server.sh
#   3. ./setup-server.sh
# =============================================================================

set -e

echo "============================================"
echo "  Arctic Debate Card Agent - Server Setup"
echo "============================================"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS"
    exit 1
fi

echo "Detected OS: $OS"

# Install Docker
echo ""
echo ">>> Installing Docker..."
if [ "$OS" = "amzn" ] || [ "$OS" = "amazon" ]; then
    # Amazon Linux 2023
    sudo dnf update -y
    sudo dnf install -y docker git
elif [ "$OS" = "ubuntu" ]; then
    # Ubuntu
    sudo apt-get update
    sudo apt-get install -y docker.io git
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
echo ""
echo ">>> Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
echo ""
echo ">>> Verifying installations..."
docker --version
docker-compose --version

# Create app directory
echo ""
echo ">>> Creating app directory..."
sudo mkdir -p /opt/arctic-debate
sudo chown $USER:$USER /opt/arctic-debate

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Log out and log back in (for docker group)"
echo "  2. cd /opt/arctic-debate"
echo "  3. Clone your repo or copy files"
echo "  4. Create .env file with your secrets"
echo "  5. Run: docker-compose up -d --build"
echo ""
echo "Important: You may need to re-login for docker permissions"
echo ""

