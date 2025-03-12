"""
Tomato.gg Selenium Web Scraper

This script uses Selenium to scrape player game data from tomato.gg,
which is useful for content that's loaded dynamically with JavaScript.
"""

import time
import random
import os
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openpyxl import Workbook

# Constants
BASE_URL = "https://tomato.gg"

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def create_data_directory():
    """Create a directory to store scraped data if it doesn't exist."""
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created 'data' directory")

def handle_cookie_consent(driver):
    """
    Handle the cookie consent popup if it appears.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
    """
    try:
        # Wait for the cookie consent popup
        cookie_popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "qc-cmp-cleanslate"))
        )
        
        # Try to find and click the accept button
        try:
            accept_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Accept') or contains(text(), 'Agree') or contains(text(), 'I Accept')]")
            accept_button.click()
            time.sleep(2)  # Wait for popup to disappear
            print("Accepted cookie consent")
        except:
            print("Could not find accept button in cookie popup")
            
            # Try to click the popup itself to dismiss it
            try:
                cookie_popup.click()
                time.sleep(2)
                print("Clicked cookie popup")
            except:
                print("Could not click cookie popup")
                
            # If still present, try to remove it using JavaScript
            try:
                driver.execute_script("arguments[0].remove();", cookie_popup)
                print("Removed cookie popup via JavaScript")
            except:
                print("Could not remove cookie popup")
    except:
        print("No cookie consent popup found")

def get_player_page(driver, player_name, server="na", player_id=None):
    """
    Navigate to a player's page using Selenium.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        player_name (str): The player's username
        server (str): Server region (na, eu, asia, etc.)
        player_id (str, optional): Player's ID number if known
    """
    if player_id:
        # Use the exact URL format from the user's link
        url = f"{BASE_URL}/stats/{player_name}-{player_id}/{server}?tab=main"
    else:
        url = f"{BASE_URL}/player/{server}/{player_name}"
        
    print(f"Navigating to: {url}")
    
    try:
        driver.get(url)
        # Wait for the page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Handle cookie consent popup
        handle_cookie_consent(driver)
        
        # Additional wait for dynamic content
        time.sleep(8)
        
        # Scroll down to the recent battles section
        print("Scrolling down to find recent battles...")
        for _ in range(3):  # Scroll down a few times
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
            
    except Exception as e:
        print(f"Error loading player page: {e}")

def extract_player_stats(driver):
    """
    Extract basic player statistics using Selenium.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        
    Returns:
        dict: Player statistics
    """
    stats = {}
    
    try:
        # Try to find player name
        try:
            stats["player_name"] = driver.find_element(By.CSS_SELECTOR, "h1, .player-name, .username").text.strip()
        except:
            # Try to get from title
            stats["player_name"] = driver.title.split("[")[0].strip()
        
        # Try to find WN8 rating
        try:
            wn8_element = driver.find_element(By.XPATH, "//*[contains(text(), 'WN8')]/following-sibling::*")
            stats["wn8"] = wn8_element.text.strip()
        except:
            print("Could not find WN8")
        
        # Try to find win rate
        try:
            winrate_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Win Rate')]/following-sibling::*")
            stats["win_rate"] = winrate_element.text.strip()
        except:
            print("Could not find win rate")
        
        # Try to find battles count
        try:
            battles_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Battles')]/following-sibling::*")
            stats["battles"] = battles_element.text.strip()
        except:
            print("Could not find battles count")
        
        # Try to find average damage
        try:
            avg_dmg_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Avg Damage')]/following-sibling::*")
            stats["avg_damage"] = avg_dmg_element.text.strip()
        except:
            print("Could not find average damage")
        
        # If we couldn't find any stats, print page source to help debug
        if len(stats) <= 1:  # Only player name found
            print("Could not find most player stats. Taking screenshot for debugging...")
            driver.save_screenshot("data/debug_screenshot.png")
            print("Screenshot saved to data/debug_screenshot.png")
        
    except Exception as e:
        print(f"Error extracting player stats: {e}")
    
    return stats

def extract_battle_details(driver, battle_element):
    """
    Extract detailed information from a battle by clicking on it.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        battle_element: The battle element to click
        
    Returns:
        dict: Detailed battle information
    """
    battle_details = {}
    
    try:
        # Click on the battle element
        print("Clicking on battle to view details...")
        
        # Try to click using JavaScript if normal click fails
        try:
            battle_element.click()
        except:
            print("Regular click failed, trying JavaScript click...")
            driver.execute_script("arguments[0].click();", battle_element)
            
        time.sleep(3)  # Wait for details to load
        
        # Wait for the details to appear
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Team Score') or contains(text(), 'Battle Result')]"))
            )
        except:
            print("Battle details might not have loaded properly")
        
        # Debugging: Take a screenshot of the details for debugging
        driver.save_screenshot("data/battle_details_debug.png")
        print("Saved battle details screenshot to data/battle_details_debug.png")
        
        # Extract the battle link
        try:
            print("Attempting to find battle link...")
            battle_link_element = driver.find_element(By.XPATH, "//a[contains(@href, '/battle/')]")
            battle_link = battle_link_element.get_attribute('href')
            print(f"Found battle link: {battle_link}")
            
            # Navigate to the battle link
            driver.get(battle_link)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Team Score') or contains(text(), 'Battle Result')]"))
            )
            
            # Extract team stats
            team_stats_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'team-stats')]//tr")
            teams = {"team1": [], "team2": []}
            for element in team_stats_elements:
                player_data = {}
                try:
                    # Extract player name
                    name_element = element.find_element(By.XPATH, ".//td[1]")
                    player_data["name"] = name_element.text.strip()
                    
                    # Extract player stats
                    stats_elements = element.find_elements(By.XPATH, ".//td[position()>1]")
                    for i, stat in enumerate(stats_elements):
                        player_data[f"stat_{i}"] = stat.text.strip()
                    
                    # Determine which team based on element position or class
                    if "team1" in element.get_attribute("class"):
                        teams["team1"].append(player_data)
                    else:
                        teams["team2"].append(player_data)
                except Exception as e:
                    print(f"Error extracting player data: {e}")
            
            battle_details["teams"] = teams
        except Exception as e:
            print(f"Error extracting battle link or team stats: {e}")
        
        # Print what we found for debugging
        print("\nExtracted battle details:")
        print(json.dumps(battle_details, indent=2))
        
    except Exception as e:
        print(f"Error extracting battle details: {e}")
    
    return battle_details

def extract_recent_battles(driver):
    """
    Extract data about recent battles using Selenium.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        
    Returns:
        list: List of dictionaries containing battle data
    """
    battles = []
    
    try:
        # Based on the screenshot, we're looking for battle entries that have map names, times, and stats
        print("Looking for battle entries...")
        
        # Try to find the Berlin battle specifically (most recent)
        berlin_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Berlin')]")
        
        if berlin_elements:
            print("Found Berlin battle, attempting to extract details...")
            
            # Get the container element for the Berlin battle
            berlin_battle = None
            for element in berlin_elements:
                try:
                    # Go up a few levels to find the clickable container
                    parent = element
                    for _ in range(4):  # Try going up to 4 levels up
                        if parent:
                            parent = parent.find_element(By.XPATH, "..")
                            # Check if this is the battle container
                            if "Grille" in parent.text:
                                berlin_battle = parent
                                break
                except:
                    continue
            
            if berlin_battle:
                print("Found Berlin battle container, extracting details...")
                
                # Extract basic battle info
                battle_data = {
                    "map": "Berlin",
                    "tank": "Grille 15",
                    "time": "15 hours ago"
                }
                
                # Get detailed battle information
                details = extract_battle_details(driver, berlin_battle)
                battle_data.update(details)
                
                battles.append(battle_data)
            else:
                print("Could not find the complete Berlin battle container")
        else:
            print("Could not find the Berlin battle")
            
    except Exception as e:
        print(f"Error extracting battle data: {e}")
    
    return battles

def save_to_json(data, filename):
    """
    Save the extracted data to a JSON file.
    
    Args:
        data (list): List of dictionaries containing data
        filename (str): Name of the output file
    """
    if not data:
        print("No data to save")
        return
    
    try:
        filepath = os.path.join("data", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data saved to JSON: {filepath}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

def save_to_csv_manually(data, filename):
    """
    Save the extracted data to a CSV file without using pandas.
    
    Args:
        data (list): List of dictionaries containing data
        filename (str): Name of the output file
    """
    if not data or len(data) == 0:
        print("No data to save")
        return
    
    try:
        filepath = os.path.join("data", filename)
        
        # Get all possible headers from all dictionaries
        headers = set()
        for item in data:
            headers.update(item.keys())
        headers = sorted(list(headers))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write headers
            f.write(','.join(headers) + '\n')
            
            # Write data
            for item in data:
                row = []
                for header in headers:
                    # Get value or empty string if key doesn't exist
                    value = str(item.get(header, ''))
                    # Escape commas and quotes
                    if ',' in value or '"' in value:
                        value = '"' + value.replace('"', '""') + '"'
                    row.append(value)
                f.write(','.join(row) + '\n')
                
        print(f"Data saved to CSV: {filepath}")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")

def extract_battle_stats_from_link(driver, battle_link):
    """
    Extract player stats from a specific battle link.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        battle_link (str): URL of the battle page
        
    Returns:
        list: List of dictionaries containing player stats
    """
    player_stats = []
    
    try:
        # Navigate to the battle link
        print(f"Navigating to battle link: {battle_link}")
        driver.get(battle_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Team Score') or contains(text(), 'Final Score')]"))
        )
        
        # Extract player stats
        team_stats_elements = driver.find_elements(By.XPATH, "//table[contains(@class, 'team-stats')]//tr")
        for element in team_stats_elements:
            player_data = {}
            try:
                # Extract tank name
                tank_element = element.find_element(By.XPATH, ".//td[1]")
                player_data["tank"] = tank_element.text.strip()
                
                # Extract player name
                name_element = element.find_element(By.XPATH, ".//td[2]")
                player_data["name"] = name_element.text.strip()
                
                # Extract damage
                damage_element = element.find_element(By.XPATH, ".//td[3]")
                player_data["damage"] = damage_element.text.strip()
                
                player_stats.append(player_data)
            except Exception as e:
                print(f"Error extracting player data: {e}")
    except Exception as e:
        print(f"Error navigating to battle link or extracting stats: {e}")
    
    return player_stats

def save_to_excel(data, filename):
    """
    Save the extracted data to an Excel file.
    
    Args:
        data (list): List of dictionaries containing data
        filename (str): Name of the output file
    """
    if not data:
        print("No data to save")
        return
    
    try:
        filepath = os.path.join("data", filename)
        workbook = Workbook()
        sheet = workbook.active
        
        # Write headers
        headers = data[0].keys()
        sheet.append(headers)
        
        # Write data
        for item in data:
            sheet.append(item.values())
        
        workbook.save(filepath)
        print(f"Data saved to Excel: {filepath}")
    except Exception as e:
        print(f"Error saving data to Excel: {e}")

def main():
    """Main function to run the Selenium scraper."""
    create_data_directory()
    
    driver = setup_driver()
    
    try:
        # Use the provided battle link
        battle_link = "https://tomato.gg/battle/97429530965048181/512317641"
        
        # Extract player stats from the battle link
        player_stats = extract_battle_stats_from_link(driver, battle_link)
        
        # Save data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_to_excel(player_stats, f"battle_stats_{timestamp}.xlsx")
        
        print("\nData extraction complete!")
        print(f"Battle stats saved to: data/battle_stats_{timestamp}.xlsx")
    
    finally:
        # Always close the driver
        driver.quit()
        print("Driver closed")

if __name__ == "__main__":
    main() 