#!/bin/bash

# Create chrome directory if it doesn't exist
mkdir -p /opt/render/project/src/chrome
cd /opt/render/project/src/chrome

# Install Chrome dependencies
sudo apt-get update
sudo apt-get install -y wget unzip xvfb libxi6 libgconf-2-4 default-jdk

# Download and install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb

# Get Chrome version and install matching ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Extract major version
CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
echo "Chrome major version: $CHROME_MAJOR_VERSION"

# Download matching ChromeDriver
wget "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
unzip chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver .
chmod +x chromedriver

# Verify installations
echo "Chrome version:"
google-chrome --version
echo "ChromeDriver version:"
./chromedriver --version

# Clean up
rm -rf chromedriver-linux64 chromedriver-linux64.zip google-chrome-stable_current_amd64.deb

# Make Chrome and ChromeDriver available in PATH
export PATH="/opt/render/project/src/chrome:$PATH" 