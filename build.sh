#!/bin/bash

# Create chrome directory
CHROME_DIR="/opt/render/project/src/chrome"
mkdir -p "$CHROME_DIR"
cd "$CHROME_DIR"

echo "Current directory: $(pwd)"
echo "Contents before installation:"
ls -la

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y wget unzip fontconfig fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2 libdbus-1-3 libdrm2 libexpat1 libgbm1 libglib2.0-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 xdg-utils

# Download and install Chrome
echo "Downloading Chrome..."
wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"

# Install Chrome package
echo "Installing Chrome..."
dpkg -i google-chrome-stable_current_amd64.deb || true
apt-get install -f -y

# Create symlinks to the installed Chrome
echo "Creating symlinks..."
ln -sf /usr/bin/google-chrome-stable "${PWD}/google-chrome-stable"
ln -sf /usr/bin/google-chrome-stable "${PWD}/google-chrome"

# Set permissions
echo "Setting permissions..."
chmod +x "${PWD}/google-chrome-stable"
chmod +x "${PWD}/google-chrome"

# Get Chrome version
CHROME_VERSION=$(google-chrome-stable --version | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Download ChromeDriver
echo "Downloading ChromeDriver..."
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"
curl -L -o chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver.zip
chmod +x chromedriver

# Clean up
echo "Cleaning up..."
rm -f google-chrome-stable_current_amd64.deb chromedriver.zip

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
ls -la google-chrome*
file google-chrome-stable
which google-chrome-stable

echo "Chrome version check:"
google-chrome-stable --version || echo "Failed to get Chrome version"
./google-chrome --version || echo "Failed to get Chrome version"

echo "ChromeDriver version check:"
./chromedriver --version || echo "Failed to get ChromeDriver version"

echo "Contents after installation:"
ls -la

# Create a file to indicate successful installation
touch .chrome_installed

# Export the Chrome directory path
echo "export CHROME_DIR=${CHROME_DIR}" >> $HOME/.bashrc
echo "export PATH=${CHROME_DIR}:$PATH" >> $HOME/.bashrc

# Verify Chrome can start
echo "Testing Chrome..."
timeout 10s google-chrome-stable --version --no-sandbox --headless || echo "Chrome test failed" 