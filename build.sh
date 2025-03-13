#!/bin/bash

# Create chrome directory if it doesn't exist
mkdir -p /opt/render/project/src/chrome
cd /opt/render/project/src/chrome

# Install Chrome dependencies
apt-get update
apt-get install -y wget unzip xvfb libxi6 libgconf-2-4 default-jdk

# Download and install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Get Chrome version and install matching ChromeDriver
CHROME_VERSION=$(google-chrome-stable --version | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Extract major version
CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
echo "Chrome major version: $CHROME_MAJOR_VERSION"

# Download matching ChromeDriver
wget "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
unzip chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver .
chmod +x chromedriver

# Create symlink to Chrome binary
ln -s /usr/bin/google-chrome-stable google-chrome

# Verify installations and paths
echo "Chrome binary location:"
which google-chrome-stable
ls -l google-chrome
echo "ChromeDriver location:"
ls -l chromedriver
echo "Chrome version:"
google-chrome-stable --version
echo "ChromeDriver version:"
./chromedriver --version

# Clean up
rm -rf chromedriver-linux64 chromedriver-linux64.zip google-chrome-stable_current_amd64.deb

# Make Chrome and ChromeDriver available in PATH
export PATH="/opt/render/project/src/chrome:$PATH" 