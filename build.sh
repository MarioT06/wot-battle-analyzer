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
sudo apt-get update || { echo "Failed to update apt"; exit 1; }
sudo apt-get install -y wget unzip fontconfig fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2 libdbus-1-3 libdrm2 libexpat1 libgbm1 libglib2.0-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 xdg-utils || { echo "Failed to install dependencies"; exit 1; }

# Add Google Chrome repository and key
echo "Adding Google Chrome repository..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update package list and install Chrome
echo "Updating package list and installing Chrome..."
sudo apt-get update || { echo "Failed to update apt after adding Chrome repo"; exit 1; }
sudo apt-get install -y google-chrome-stable || { echo "Failed to install Chrome"; exit 1; }

# Create symlinks to the installed Chrome
echo "Creating symlinks..."
sudo ln -sf /usr/bin/google-chrome-stable "${PWD}/google-chrome-stable"
sudo ln -sf /usr/bin/google-chrome-stable "${PWD}/google-chrome"

# Set permissions
echo "Setting permissions..."
sudo chmod +x "${PWD}/google-chrome-stable"
sudo chmod +x "${PWD}/google-chrome"
sudo chmod 755 "${PWD}"

# Get Chrome version
CHROME_VERSION=$(google-chrome-stable --version 2>/dev/null || /usr/bin/google-chrome-stable --version)
echo "Chrome version: $CHROME_VERSION"

# Download ChromeDriver
echo "Downloading ChromeDriver..."
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"
curl -L -o chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver.zip
chmod +x chromedriver

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
ls -la /usr/bin/google-chrome* || echo "No Chrome binaries in /usr/bin"
ls -la "${PWD}/google-chrome*" || echo "No Chrome binaries in ${PWD}"
file /usr/bin/google-chrome-stable || echo "Could not inspect Chrome binary"
which google-chrome-stable || echo "Chrome not in PATH"

echo "Chrome version check:"
/usr/bin/google-chrome-stable --version --no-sandbox || echo "Failed to get Chrome version from /usr/bin"
"${PWD}/google-chrome" --version --no-sandbox || echo "Failed to get Chrome version from symlink"

echo "ChromeDriver version check:"
./chromedriver --version || echo "Failed to get ChromeDriver version"

echo "Contents of important directories:"
echo "/usr/bin contents:"
ls -la /usr/bin/google-chrome* || echo "No Chrome files in /usr/bin"
echo
echo "Current directory contents:"
ls -la

# Create a file to indicate successful installation
touch .chrome_installed

# Export the Chrome directory path
echo "export CHROME_DIR=${CHROME_DIR}" >> $HOME/.bashrc
echo "export PATH=/usr/bin:${CHROME_DIR}:$PATH" >> $HOME/.bashrc

# Verify Chrome installation
echo "Testing Chrome..."
/usr/bin/google-chrome-stable --version --no-sandbox --headless || echo "Chrome test failed from /usr/bin"
"${PWD}/google-chrome" --version --no-sandbox --headless || echo "Chrome test failed from symlink"

# Print final status
if [ -x /usr/bin/google-chrome-stable ] && [ -x "${PWD}/chromedriver" ]; then
    echo "Installation completed successfully"
else
    echo "Installation may have failed"
    exit 1
fi 