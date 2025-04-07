#!/bin/bash

# Script to install Docker Engine on Ubuntu 24.04
# Run this script with sudo privileges (sudo ./install-docker.sh)

set -e

# Print commands before executing and exit on errors
echo "Docker Engine Installation Script for Ubuntu 24.04"
echo "=================================================="

# Update package index
echo "[1/7] Updating package index..."
apt-get update

# Install required packages
echo "[2/7] Installing required packages..."
apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
echo "[3/7] Adding Docker's official GPG key..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Set up the repository
echo "[4/7] Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again with Docker repository
echo "[5/7] Updating package index with Docker repository..."
apt-get update

# Install Docker Engine
echo "[6/7] Installing Docker Engine, containerd, and Docker Compose..."
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
echo "[7/7] Verifying installation..."
docker --version
docker compose version

# Add current user to the docker group (to use Docker without sudo)
if [ "$SUDO_USER" ]; then
    echo "Adding user $SUDO_USER to the docker group..."
    usermod -aG docker $SUDO_USER
    echo "You may need to log out and log back in for this to take effect."
fi

echo ""
echo "Docker Engine has been successfully installed!"
echo "To verify the installation, run: docker run hello-world"