#!/bin/bash

# Install Chrome
curl -LO "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
sudo dpkg -i google-chrome-stable_current_amd64.deb || true
sudo apt-get update
sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}")
curl -LO "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip 