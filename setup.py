"""
Setup script for the Tomato.gg Web Scraper.
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"Python version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected.")

def install_requirements():
    """Install required packages from requirements.txt."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("All packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def create_data_directory():
    """Create data directory if it doesn't exist."""
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created 'data' directory.")

def main():
    """Main setup function."""
    print("Setting up Tomato.gg Web Scraper...")
    check_python_version()
    install_requirements()
    create_data_directory()
    print("\nSetup complete! You can now run the scraper with:")
    print("  python tomato_scraper.py")
    print("  or")
    print("  python selenium_scraper.py")

if __name__ == "__main__":
    main() 