#!/bin/bash

# Create chrome directory if it doesn't exist
mkdir -p /opt/render/project/src/chrome
cd /opt/render/project/src/chrome

# Install Chrome
curl -O https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update && apt-get install -y ./google-chrome-stable_current_amd64.deb

# Get Chrome version
CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Install matching ChromeDriver
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}")
echo "Installing ChromeDriver version: $CHROMEDRIVER_VERSION"

curl -Lo chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver.zip
chmod +x chromedriver

# Verify installations
echo "Chrome version:"
google-chrome --version
echo "ChromeDriver version:"
./chromedriver --version

# Clean up
rm google-chrome-stable_current_amd64.deb chromedriver.zip

# Export path
export PATH="/opt/render/project/src/chrome:$PATH" 