#!/bin/bash

# Create chrome directory
mkdir -p /opt/render/project/src/chrome
cd /opt/render/project/src/chrome

# Install Chrome dependencies without requiring root
echo "Installing Chrome dependencies..."
pip install wget
python3 -m wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Extract Chrome from deb package
echo "Extracting Chrome..."
mkdir -p chrome-tmp
cd chrome-tmp
ar x ../google-chrome-stable_current_amd64.deb
tar xf data.tar.xz
cd ..

# Move Chrome files to the correct location
echo "Setting up Chrome..."
mv chrome-tmp/usr/bin/google-chrome-stable .
mv chrome-tmp/usr/share/chrome* . 2>/dev/null || true
mv chrome-tmp/usr/share/google-chrome . 2>/dev/null || true

# Create necessary symlinks
echo "Creating symlinks..."
ln -sf ${PWD}/google-chrome-stable ${PWD}/google-chrome

# Get Chrome version
CHROME_VERSION=$(./google-chrome-stable --version 2>/dev/null | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Download matching ChromeDriver
echo "Downloading ChromeDriver..."
CHROMEDRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"
wget "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
chmod +x chromedriver

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
ls -la ${PWD}/google-chrome*
file ${PWD}/google-chrome-stable

echo "Chrome version check:"
${PWD}/google-chrome-stable --version || echo "Failed to get Chrome version"
${PWD}/google-chrome --version || echo "Failed to get Chrome version"

echo "ChromeDriver version check:"
./chromedriver --version || echo "Failed to get ChromeDriver version"

# Clean up
rm -rf chrome-tmp google-chrome-stable_current_amd64.deb chromedriver_linux64.zip

# Make Chrome and ChromeDriver available in PATH
export PATH="${PWD}:${PATH}"

# Final verification
echo "Final PATH: $PATH"
echo "Final verification:"
which google-chrome || echo "google-chrome not found in PATH"
which google-chrome-stable || echo "google-chrome-stable not found in PATH"
which chromedriver || echo "chromedriver not found in PATH"

# List all files in chrome directory
echo "Contents of ${PWD}:"
ls -la 