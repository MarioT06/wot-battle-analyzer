#!/bin/bash

# Create chrome directory
CHROME_DIR="/opt/render/project/src/chrome"
mkdir -p "$CHROME_DIR"
cd "$CHROME_DIR"

echo "Current directory: $(pwd)"
echo "Contents before installation:"
ls -la

# Download Chrome package
echo "Downloading Chrome..."
curl -o chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Extract Chrome
echo "Extracting Chrome..."
ar x chrome.deb
tar xf data.tar.xz

# Move Chrome binary to the correct location
echo "Setting up Chrome..."
mv usr/bin/google-chrome-stable .
mv usr/share/chrome* . 2>/dev/null || true
mv usr/share/google-chrome . 2>/dev/null || true

# Create symlink
echo "Creating symlinks..."
ln -sf "${PWD}/google-chrome-stable" "${PWD}/google-chrome"

# Set permissions
echo "Setting permissions..."
chmod +x google-chrome-stable
chmod +x google-chrome

# Get Chrome version
CHROME_VERSION=$(./google-chrome-stable --version 2>/dev/null | cut -d ' ' -f 3)
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
rm -rf usr/ chrome.deb data.tar.* control.tar.* debian-binary chromedriver.zip

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
ls -la google-chrome*
file google-chrome-stable

echo "Chrome version check:"
./google-chrome-stable --version || echo "Failed to get Chrome version"
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