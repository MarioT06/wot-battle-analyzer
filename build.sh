#!/bin/bash

# Create chrome directory
CHROME_DIR="/opt/render/project/src/chrome"
mkdir -p "$CHROME_DIR"
cd "$CHROME_DIR"

echo "Current directory: $(pwd)"
echo "Contents before installation:"
ls -la

# Download Chrome
echo "Downloading Chrome..."
curl -L -o chrome.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chrome-linux64.zip"

# Extract Chrome
echo "Extracting Chrome..."
unzip -q chrome.zip
mv chrome-linux64/* .
rmdir chrome-linux64

# Set up Chrome binary
echo "Setting up Chrome binary..."
chmod +x chrome
ln -sf "${PWD}/chrome" "${PWD}/google-chrome"
ln -sf "${PWD}/chrome" "${PWD}/google-chrome-stable"

# Download ChromeDriver
echo "Downloading ChromeDriver..."
curl -L -o chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/120.0.6099.109/linux64/chromedriver-linux64.zip"
unzip -q chromedriver.zip
mv chromedriver-linux64/chromedriver .
rmdir chromedriver-linux64

# Set permissions
echo "Setting permissions..."
chmod +x chrome google-chrome google-chrome-stable chromedriver
chmod 755 "${PWD}"

# Clean up
echo "Cleaning up..."
rm -f chrome.zip chromedriver.zip

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
ls -la chrome* google-chrome*
file chrome
file chromedriver

echo "Chrome version check:"
./chrome --version --no-sandbox || echo "Failed to get Chrome version"
./google-chrome --version --no-sandbox || echo "Failed to get Chrome version from symlink"

echo "ChromeDriver version check:"
./chromedriver --version || echo "Failed to get ChromeDriver version"

echo "Contents after installation:"
ls -la

# Create a file to indicate successful installation
touch .chrome_installed

# Export the Chrome directory path
echo "export CHROME_DIR=${CHROME_DIR}" >> $HOME/.bashrc
echo "export PATH=${CHROME_DIR}:$PATH" >> $HOME/.bashrc

# Verify Chrome installation
echo "Testing Chrome..."
./chrome --version --no-sandbox --headless || echo "Chrome test failed"

# Print final status
if [ -x "${PWD}/chrome" ] && [ -x "${PWD}/chromedriver" ]; then
    echo "Installation completed successfully"
else
    echo "Installation may have failed"
    exit 1
fi 