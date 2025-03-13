#!/bin/bash

# Create chrome directory if it doesn't exist
mkdir -p /opt/render/project/src/chrome
cd /opt/render/project/src/chrome

# Add Google Chrome repository and install Chrome
echo "Adding Google Chrome repository..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Chrome and dependencies
echo "Installing Chrome and dependencies..."
apt-get update
apt-get install -y wget unzip xvfb libxi6 libgconf-2-4 default-jdk google-chrome-stable

# Get Chrome version
CHROME_VERSION=$(google-chrome-stable --version | cut -d ' ' -f 3)
echo "Chrome version: $CHROME_VERSION"

# Extract major version
CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
echo "Chrome major version: $CHROME_MAJOR_VERSION"

# Download matching ChromeDriver
echo "Downloading ChromeDriver..."
wget "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
unzip chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver .
chmod +x chromedriver

# Create symlinks and verify installations
echo "Creating symlinks and verifying installations..."
ln -sf /usr/bin/google-chrome-stable /opt/render/project/src/chrome/google-chrome
ln -sf /usr/bin/google-chrome-stable google-chrome-stable

# Print debug information
echo "Debug information:"
echo "Chrome binary locations:"
which google-chrome-stable
which google-chrome
ls -l /usr/bin/google-chrome*
ls -l /opt/render/project/src/chrome/

echo "Chrome version check:"
google-chrome-stable --version
/opt/render/project/src/chrome/google-chrome --version

echo "ChromeDriver version check:"
./chromedriver --version

# Clean up
rm -rf chromedriver-linux64 chromedriver-linux64.zip

# Make Chrome and ChromeDriver available in PATH
export PATH="/opt/render/project/src/chrome:$PATH"

# Final verification
echo "Final PATH: $PATH"
echo "Final verification:"
which google-chrome
which google-chrome-stable
which chromedriver 