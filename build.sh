#!/bin/bash

# Create chrome directory
mkdir -p /opt/render/project/src/chrome
cd /opt/render/project/src/chrome

# Download and install Chrome directly
echo "Downloading Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
ar x google-chrome-stable_current_amd64.deb
tar xf data.tar.xz

# Get Chrome version from the binary
CHROME_VERSION=$(./usr/bin/google-chrome-stable --version 2>/dev/null | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Download matching ChromeDriver
echo "Downloading ChromeDriver..."
wget "https://chromedriver.storage.googleapis.com/LATEST_RELEASE" -O chrome_version
CHROMEDRIVER_VERSION=$(cat chrome_version)
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"
wget "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
chmod +x chromedriver

# Create symlinks
echo "Creating symlinks..."
ln -sf ${PWD}/usr/bin/google-chrome-stable ${PWD}/google-chrome
ln -sf ${PWD}/usr/bin/google-chrome-stable ${PWD}/google-chrome-stable

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
ls -l ${PWD}/usr/bin/google-chrome*
ls -l ${PWD}/google-chrome*

echo "Chrome version check:"
${PWD}/usr/bin/google-chrome-stable --version
${PWD}/google-chrome --version

echo "ChromeDriver version check:"
./chromedriver --version

# Clean up
rm -f google-chrome-stable_current_amd64.deb data.tar.xz control.tar.xz debian-binary chrome_version chromedriver_linux64.zip

# Make Chrome and ChromeDriver available in PATH
export PATH="${PWD}:${PATH}"

# Final verification
echo "Final PATH: $PATH"
echo "Final verification:"
which google-chrome
which google-chrome-stable
which chromedriver 