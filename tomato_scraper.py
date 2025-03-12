"""
Tomato.gg Web Scraper

This script scrapes player game data from tomato.gg, a World of Tanks statistics website.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
from datetime import datetime

# Constants
BASE_URL = "https://tomato.gg"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def create_data_directory():
    """Create a directory to store scraped data if it doesn't exist."""
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created 'data' directory")

def get_player_page(player_name, server="na", player_id=None):
    """
    Fetch the HTML content of a player's page.
    
    Args:
        player_name (str): The player's username
        server (str): Server region (na, eu, asia, etc.)
        player_id (str, optional): Player's ID number if known
        
    Returns:
        BeautifulSoup object or None if request fails
    """
    if player_id:
        url = f"{BASE_URL}/stats/{server}/{player_name}={player_id}"
    else:
        url = f"{BASE_URL}/player/{server}/{player_name}"
    
    print(f"Fetching data from: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player page: {e}")
        return None

def extract_player_stats(soup):
    """
    Extract basic player statistics from the BeautifulSoup object.
    
    Args:
        soup (BeautifulSoup): Parsed HTML of player page
        
    Returns:
        dict: Player statistics
    """
    if not soup:
        return {}
    
    stats = {}
    
    try:
        # Try to find player name
        player_name_selectors = [".player-name", ".username", "h1", "title"]
        for selector in player_name_selectors:
            element = soup.select_one(selector)
            if element:
                stats["player_name"] = element.text.strip()
                break
        
        # Try to find WN8 rating
        wn8_selectors = [".wn8-value", ".wn8", "[data-stat='wn8']", ".rating"]
        for selector in wn8_selectors:
            element = soup.select_one(selector)
            if element:
                stats["wn8"] = element.text.strip()
                break
        
        # Try to find win rate
        winrate_selectors = [".winrate-value", ".winrate", "[data-stat='winRate']", ".win-rate"]
        for selector in winrate_selectors:
            element = soup.select_one(selector)
            if element:
                stats["win_rate"] = element.text.strip()
                break
        
        # Try to find battles count
        battles_selectors = [".battles-value", ".battles", "[data-stat='battles']", ".battle-count"]
        for selector in battles_selectors:
            element = soup.select_one(selector)
            if element:
                stats["battles"] = element.text.strip()
                break
        
        # Try to find average damage
        avg_dmg_selectors = [".avg-damage-value", ".avg-damage", "[data-stat='avgDamage']", ".average-damage"]
        for selector in avg_dmg_selectors:
            element = soup.select_one(selector)
            if element:
                stats["avg_damage"] = element.text.strip()
                break
        
        # If we couldn't find any stats, print part of the HTML to help debug
        if not stats:
            print("Could not find player stats. HTML structure:")
            print(soup.prettify()[:1000])  # Print first 1000 chars to avoid overwhelming output
        
    except Exception as e:
        print(f"Error extracting player stats: {e}")
    
    return stats

def extract_recent_battles(soup):
    """
    Extract data about recent battles from the player page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML of player page
        
    Returns:
        list: List of dictionaries containing battle data
    """
    if not soup:
        return []
    
    battles = []
    
    try:
        # Look for the recent battles section
        # Note: These selectors are educated guesses and may need adjustment
        # after inspecting the actual HTML of tomato.gg
        
        # First try to find a table or container with recent battles
        battle_containers = soup.select(".session-table tbody tr, .battle-history-item, .recent-battle-item")
        
        if not battle_containers:
            print("Could not find battle containers with initial selectors, trying alternatives...")
            # Try alternative selectors
            battle_containers = soup.select("table.recent-battles tr, div.battle-history div.battle-item")
        
        if not battle_containers:
            # If still not found, dump the HTML structure to help debug
            print("Could not find battle containers. HTML structure:")
            print(soup.prettify()[:1000])  # Print first 1000 chars to avoid overwhelming output
            return []
            
        print(f"Found {len(battle_containers)} battle containers")
        
        for battle in battle_containers:
            # Try different possible selectors for each piece of data
            battle_data = {}
            
            # Tank
            tank_element = battle.select_one(".tank-name, .vehicle-name, .tank, img[alt*='tank']")
            if tank_element:
                if tank_element.name == 'img' and tank_element.get('alt'):
                    battle_data["tank"] = tank_element['alt']
                else:
                    battle_data["tank"] = tank_element.text.strip()
            else:
                battle_data["tank"] = "Unknown"
                
            # Map
            map_element = battle.select_one(".map-name, .map, .battle-map")
            if map_element:
                battle_data["map"] = map_element.text.strip()
            else:
                battle_data["map"] = "Unknown"
                
            # Result (Victory/Defeat)
            result_element = battle.select_one(".battle-result, .result, .victory, .defeat, .draw")
            if result_element:
                battle_data["result"] = result_element.text.strip()
            else:
                # Try to infer from class names
                if 'victory' in battle.get('class', []) or 'win' in battle.get('class', []):
                    battle_data["result"] = "Victory"
                elif 'defeat' in battle.get('class', []) or 'loss' in battle.get('class', []):
                    battle_data["result"] = "Defeat"
                else:
                    battle_data["result"] = "Unknown"
                
            # Damage
            damage_element = battle.select_one(".damage, .damage-value, .battle-damage")
            if damage_element:
                battle_data["damage"] = damage_element.text.strip()
            else:
                battle_data["damage"] = "Unknown"
                
            # Date/Time
            date_element = battle.select_one(".battle-date, .date, .time, .timestamp")
            if date_element:
                battle_data["date"] = date_element.text.strip()
            else:
                battle_data["date"] = "Unknown"
                
            # Additional stats you might want
            # XP
            xp_element = battle.select_one(".xp, .experience, .battle-xp")
            if xp_element:
                battle_data["xp"] = xp_element.text.strip()
                
            # Kills
            kills_element = battle.select_one(".kills, .frags, .battle-kills")
            if kills_element:
                battle_data["kills"] = kills_element.text.strip()
                
            # Spots
            spots_element = battle.select_one(".spots, .spotted, .battle-spots")
            if spots_element:
                battle_data["spots"] = spots_element.text.strip()
            
            battles.append(battle_data)
            
        # If we found battles but some data is missing, print the HTML of the first battle
        # to help with debugging
        if battles and all(value == "Unknown" for value in battles[0].values()):
            print("Found battles but couldn't extract data. First battle HTML:")
            print(battle_containers[0].prettify())
            
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
                        value = f'"{value.replace('"', '""')}"'
                    row.append(value)
                f.write(','.join(row) + '\n')
                
        print(f"Data saved to CSV: {filepath}")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")

def main():
    """Main function to run the scraper."""
    create_data_directory()
    
    # Set the player name to TheTankreaper with correct capitalization and ID
    player_name = "TheTankreaper"
    player_id = "512317641"
    server = "EU"
    
    all_player_stats = []
    all_battles = []
    
    print(f"\nProcessing player: {player_name}")
    
    # Get player page using the exact URL format
    soup = get_player_page(player_name, server, player_id)
    
    # Extract data
    player_stats = extract_player_stats(soup)
    if player_stats:
        all_player_stats.append(player_stats)
    
    battles = extract_recent_battles(soup)
    # Limit to last 10 battles
    battles = battles[:10]
    for battle in battles:
        battle["player"] = player_name
        all_battles.append(battle)
    
    # Save data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_to_json(all_player_stats, f"player_stats_{timestamp}.json")
    save_to_json(all_battles, f"recent_battles_{timestamp}.json")
    save_to_csv_manually(all_player_stats, f"player_stats_{timestamp}.csv")
    save_to_csv_manually(all_battles, f"recent_battles_{timestamp}.csv")
    
    print("\nData extraction complete!")
    print(f"Player stats saved to: data/player_stats_{timestamp}.json and .csv")
    print(f"Recent battles saved to: data/recent_battles_{timestamp}.json and .csv")
    print("\nYou can open the CSV files directly in Excel.")

if __name__ == "__main__":
    main() 