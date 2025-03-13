#!/bin/bash

# Create directories for Chrome and ChromeDriver
mkdir -p $HOME/chrome
mkdir -p $HOME/chromedriver

# Download and extract Chrome
curl -o $HOME/chrome/chrome.zip "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1097615%2Fchrome-linux.zip?alt=media"
unzip $HOME/chrome/chrome.zip -d $HOME/chrome/
rm $HOME/chrome/chrome.zip

# Download and setup ChromeDriver
CHROMEDRIVER_VERSION="114.0.5735.90"  # Using a stable version
curl -Lo $HOME/chromedriver/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip $HOME/chromedriver/chromedriver.zip -d $HOME/chromedriver/
chmod +x $HOME/chromedriver/chromedriver
rm $HOME/chromedriver/chromedriver.zip

# Add Chrome and ChromeDriver to PATH
export PATH=$HOME/chrome/chrome-linux:$HOME/chromedriver:$PATH 