from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import logging
import os
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    chrome_options = Options()
    # Enable headless mode
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')  # Only show fatal errors
    chrome_options.add_argument('--window-size=1920,1080')  # Set a large window size
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def extract_battle_data(driver, battle_url):
    logger.info(f"Accessing battle page: {battle_url}")
    try:
        driver.get(battle_url)
        
        # Wait for page to load
        logger.info("Waiting for page to load...")
        time.sleep(15)
        
        # Try different table selectors
        table_selectors = [
            "table",  # Try simplest first
            "div table",
            "div.battle-table table",
            "//table",  # Try XPath
            "//div//table"
        ]
        
        table = None
        for selector in table_selectors:
            try:
                logger.info(f"Trying to find table with selector: {selector}")
                if selector.startswith("//"):
                    # XPath selector
                    tables = driver.find_elements(By.XPATH, selector)
                else:
                    # CSS selector
                    tables = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if tables:
                    logger.info(f"Found {len(tables)} tables with selector {selector}")
                    table = tables[0]
                    break
            except Exception as e:
                logger.warning(f"Failed with selector {selector}: {str(e)}")
                continue
        
        if not table:
            logger.error("Could not find any table")
            return []
        
        # Get all rows
        rows = table.find_elements(By.TAG_NAME, "tr")
        logger.info(f"Found {len(rows)} total rows")
        
        if len(rows) <= 1:
            logger.error("Not enough rows found in table")
            return []
        
        # Skip header row
        rows = rows[1:]
        logger.info(f"Processing {len(rows)} data rows")
        
        battle_data = []
        for row_index, row in enumerate(rows, 1):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                logger.info(f"Row {row_index} has {len(cells)} cells")
                
                # Log all cell contents for debugging
                cell_texts = [cell.text.strip() for cell in cells]
                logger.info(f"Row {row_index} cell contents: {cell_texts}")
                
                if len(cells) < 10:
                    logger.warning(f"Row {row_index} has insufficient cells: {len(cells)}")
                    continue
                
                # Get player name and tank name directly from text
                player_name = cells[2].text.strip()
                tank_name = cells[1].text.strip()
                
                logger.info(f"Row {row_index} - Player: '{player_name}', Tank: '{tank_name}'")
                
                if not player_name or not tank_name:
                    logger.warning(f"Missing data in row {row_index}")
                    continue
                
                # Extract stats
                stats = {
                    'Name': player_name,
                    'Tank': tank_name,
                    'Damage': '0',
                    'Frags': '0',
                    'Assist': '0',
                    'Spots': '0',
                    'Accuracy': '',
                    'Survival': '',
                    'XP': '0'
                }
                
                # Extract stats from cells
                if len(cells) >= 10:
                    stats['Damage'] = ''.join(filter(str.isdigit, cells[3].text.strip())) or '0'
                    stats['Frags'] = ''.join(filter(str.isdigit, cells[4].text.strip())) or '0'
                    stats['Assist'] = ''.join(filter(str.isdigit, cells[5].text.strip())) or '0'
                    stats['Spots'] = ''.join(filter(str.isdigit, cells[6].text.strip())) or '0'
                    stats['Accuracy'] = cells[7].text.strip()
                    stats['Survival'] = cells[8].text.strip()
                    stats['XP'] = ''.join(filter(str.isdigit, cells[9].text.strip())) or '0'
                
                logger.info(f"Extracted stats for row {row_index}: {stats}")
                battle_data.append(stats)
                
            except Exception as e:
                logger.warning(f"Error processing row {row_index}: {str(e)}")
                continue
        
        if not battle_data:
            logger.error("No data was extracted from any row")
        else:
            logger.info(f"Successfully extracted data from {len(battle_data)} rows")
        
        return battle_data
    
    except Exception as e:
        logger.error(f"Error accessing battle page: {str(e)}")
        return []

def save_to_excel(data, filename):
    if not data:
        logger.warning("No data to save")
        return
    
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        logger.info(f"Created DataFrame with {len(df)} rows")
        
        # Ensure columns are in the right order
        columns = ['Name', 'Tank', 'Damage', 'Frags', 'Assist', 'Spots', 'Accuracy', 'Survival', 'XP']
        df = df[columns]
        
        # Print the data to console with proper formatting
        logger.info("\nExtracted Battle Data:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.expand_frame_repr', False)
        print("\n" + "="*100)  # Add separator line
        print(df.to_string(index=False))
        print("="*100)  # Add separator line
        
        # Save to Excel with formatting
        try:
            # Create absolute path for Excel file
            excel_path = os.path.abspath(os.path.join(os.getcwd(), filename))
            logger.info(f"Attempting to save Excel file to: {excel_path}")
            
            # Create Excel writer object with xlsxwriter engine
            writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
            
            # Convert DataFrame to Excel
            df.to_excel(writer, sheet_name='Battle Stats', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Battle Stats']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4B5320',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'center'
            })
            
            number_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'num_format': '#,##0'
            })
            
            # Format all columns
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Write data with formatting
            for row in range(len(df)):
                worksheet.write(row + 1, 0, df.iloc[row]['Name'], cell_format)
                worksheet.write(row + 1, 1, df.iloc[row]['Tank'], cell_format)
                for col in range(2, len(columns)):
                    value = df.iloc[row][columns[col]]
                    if columns[col] in ['Damage', 'Frags', 'Assist', 'Spots', 'XP']:
                        try:
                            worksheet.write_number(row + 1, col, int(value), number_format)
                        except:
                            worksheet.write(row + 1, col, value, cell_format)
                    else:
                        worksheet.write(row + 1, col, value, cell_format)
            
            # Set column widths
            column_widths = {
                'A': 20,  # Name
                'B': 15,  # Tank
                'C': 12,  # Damage
                'D': 8,   # Frags
                'E': 12,  # Assist
                'F': 8,   # Spots
                'G': 12,  # Accuracy
                'H': 12,  # Survival
                'I': 10   # XP
            }
            
            for col, width in column_widths.items():
                worksheet.set_column(f'{col}:{col}', width)
            
            # Add alternating row colors
            for row in range(1, len(df) + 1, 2):
                worksheet.set_row(row, None, workbook.add_format({'bg_color': '#F0F0F0'}))
            
            # Save and close
            writer.close()
            
            # Verify file was created
            if os.path.exists(excel_path):
                file_size = os.path.getsize(excel_path)
                logger.info(f"Excel file saved successfully!")
                logger.info(f"Location: {excel_path}")
                logger.info(f"File size: {file_size:,} bytes")
            else:
                logger.error("Excel file was not created")
            
        except Exception as e:
            logger.error(f"Error saving formatted Excel: {str(e)}")
            # Fallback to simple save
            try:
                simple_path = os.path.abspath(os.path.join(os.getcwd(), filename.replace('.xlsx', '_simple.xlsx')))
                df.to_excel(simple_path, index=False)
                logger.info(f"Saved simple Excel file to: {simple_path}")
            except Exception as e2:
                logger.error(f"Error saving simple Excel file: {str(e2)}")
                # Last resort: save as CSV
                csv_path = os.path.abspath(os.path.join(os.getcwd(), filename.replace('.xlsx', '.csv')))
                df.to_csv(csv_path, index=False)
                logger.info(f"Saved data as CSV file: {csv_path}")
        
    except Exception as e:
        logger.error(f"Error preparing data for Excel: {str(e)}")
        print("\nRaw data:")
        for row in data:
            print(row)

def calculate_averages(all_battles_data):
    """Calculate average stats for each player across all battles."""
    # Initialize dictionaries to store sums and counts
    player_stats = defaultdict(lambda: {
        'battles': 0,
        'total_damage': 0,
        'total_frags': 0,
        'total_assist': 0,
        'total_spots': 0,
        'total_xp': 0,
        'tanks': set(),  # Track unique tanks played
        'accuracy_hits': 0,
        'accuracy_shots': 0,
        'accuracy_pens': 0,
        'survival_time': 0  # in seconds
    })
    
    # Process each battle's data
    for battle_data in all_battles_data:
        for player in battle_data:
            name = player['Name']
            player_stats[name]['battles'] += 1
            player_stats[name]['total_damage'] += int(player['Damage'])
            player_stats[name]['total_frags'] += int(player['Frags'])
            player_stats[name]['total_assist'] += int(player['Assist'])
            player_stats[name]['total_spots'] += int(player['Spots'])
            player_stats[name]['total_xp'] += int(player['XP'])
            player_stats[name]['tanks'].add(player['Tank'])
            
            # Process accuracy (format: "hits/shots/pens")
            try:
                hits, shots, pens = map(int, player['Accuracy'].split('/'))
                player_stats[name]['accuracy_hits'] += hits
                player_stats[name]['accuracy_shots'] += shots
                player_stats[name]['accuracy_pens'] += pens
            except:
                pass
            
            # Process survival time (format: "mm:ss")
            try:
                minutes, seconds = map(int, player['Survival'].split(':'))
                player_stats[name]['survival_time'] += minutes * 60 + seconds
            except:
                pass
    
    # Calculate averages
    averages_data = []
    for name, stats in player_stats.items():
        battles = stats['battles']
        if battles > 0:
            avg_stats = {
                'Name': name,
                'Battles': battles,
                'Avg Damage': round(stats['total_damage'] / battles, 1),
                'Avg Frags': round(stats['total_frags'] / battles, 2),
                'Avg Assist': round(stats['total_assist'] / battles, 1),
                'Avg Spots': round(stats['total_spots'] / battles, 2),
                'Avg XP': round(stats['total_xp'] / battles, 1),
                'Tanks Used': len(stats['tanks']),
                'Tank List': ', '.join(sorted(stats['tanks'])),
            }
            
            # Calculate accuracy percentages with proper averaging
            if stats['accuracy_shots'] > 0:
                # Calculate overall hit rate (total hits / total shots)
                hit_rate = min(100, (stats['accuracy_hits'] / stats['accuracy_shots']) * 100)
                # Calculate overall pen rate (total pens / total hits)
                pen_rate = min(100, (stats['accuracy_pens'] / stats['accuracy_hits']) * 100) if stats['accuracy_hits'] > 0 else 0
                avg_stats['Hit Rate'] = f"{hit_rate:.1f}%"
                avg_stats['Pen Rate'] = f"{pen_rate:.1f}%"
            else:
                avg_stats['Hit Rate'] = "N/A"
                avg_stats['Pen Rate'] = "N/A"
            
            # Calculate average survival time
            avg_survival_seconds = stats['survival_time'] / battles
            avg_stats['Avg Survival'] = f"{int(avg_survival_seconds // 60)}:{int(avg_survival_seconds % 60):02d}"
            
            averages_data.append(avg_stats)
    
    return averages_data

def save_averages_to_excel(data, filename="battle_stats_averages.xlsx"):
    if not data:
        logger.warning("No average data to save")
        return
    
    try:
        df = pd.DataFrame(data)
        
        # Set column order
        columns = [
            'Name', 'Battles', 'Avg Damage', 'Avg Frags', 'Avg Assist', 'Avg Spots',
            'Hit Rate', 'Pen Rate', 'Avg Survival', 'Avg XP', 'Tanks Used', 'Tank List'
        ]
        df = df[columns]
        
        # Print averages to console
        print("\n" + "="*120)
        print("AVERAGE STATS ACROSS ALL BATTLES")
        print("="*120)
        print(df.to_string(index=False))
        print("="*120)
        
        # Save to Excel with formatting
        excel_path = os.path.join(os.getcwd(), filename)
        writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Average Stats', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Average Stats']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B5320',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'text_wrap': True
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'num_format': '#,##0.0'
        })
        
        # Format headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths
        column_widths = {
            'A': 20,  # Name
            'B': 10,  # Battles
            'C': 12,  # Avg Damage
            'D': 10,  # Avg Frags
            'E': 12,  # Avg Assist
            'F': 10,  # Avg Spots
            'G': 10,  # Hit Rate
            'H': 10,  # Pen Rate
            'I': 12,  # Avg Survival
            'J': 10,  # Avg XP
            'K': 10,  # Tanks Used
            'L': 40,  # Tank List
        }
        
        for col, width in column_widths.items():
            worksheet.set_column(f'{col}:{col}', width)
        
        # Write data with formatting
        for row in range(len(df)):
            for col in range(len(columns)):
                value = df.iloc[row][columns[col]]
                if isinstance(value, (int, float)) and columns[col] not in ['Battles', 'Tanks Used']:
                    worksheet.write_number(row + 1, col, value, number_format)
                else:
                    worksheet.write(row + 1, col, value, cell_format)
        
        # Add alternating row colors
        for row in range(1, len(df) + 1, 2):
            worksheet.set_row(row, None, workbook.add_format({'bg_color': '#F0F0F0'}))
        
        writer.close()
        
        print(f"\nAverage stats Excel file saved to: {excel_path}")
        
    except Exception as e:
        logger.error(f"Error saving average stats to Excel: {str(e)}")

def main():
    # List of battle URLs to process
    battle_urls = [
       "https://tomato.gg/battle/28351334265692991/508371330",
       "https://tomato.gg/battle/28350612711186977/508371330",
       "https://tomato.gg/battle/23380777203966145/508371330",
       "https://tomato.gg/battle/5433092421492630/508371330",
       "https://tomato.gg/battle/18654565126676075/508371330",
       "https://tomato.gg/battle/18654685385760038/508371330",
       "https://tomato.gg/battle/20087087043746582/508371330",
       "https://tomato.gg/battle/23380425016646001/508371330",
       "https://tomato.gg/battle/20088371238967287/508371330",
    "https://tomato.gg/battle/5440118987986488/508371330",
    "https://tomato.gg/battle/20087129993417890/508371330",
    "https://tomato.gg/battle/20088246684914564/508371330",
    "https://tomato.gg/battle/20087615324721757/508371330",
    "https://tomato.gg/battle/20088208030208295/508371330",
    "https://tomato.gg/battle/18655535789281121/508371330",
    "https://tomato.gg/battle/23381391384284693/508371330",
    "https://tomato.gg/battle/23380768614026472/508371330",
    "https://tomato.gg/battle/5432336507243544/508371330",
    "https://tomato.gg/battle/18654187169548980/508371330",
    "https://tomato.gg/battle/5435798250883490/508371330",
    "https://tomato.gg/battle/5438001569106001/508371330"
       
    ]
    
    driver = setup_driver()
    all_battles_data = []
    
    try:
        # Process each battle URL
        for i, url in enumerate(battle_urls, 1):
            logger.info(f"\nProcessing battle {i} of {len(battle_urls)}")
            battle_data = extract_battle_data(driver, url)
            if battle_data:
                all_battles_data.append(battle_data)
                # Save individual battle data
                save_to_excel(battle_data, f"battle_stats_{i}.xlsx")

        logger.info(f"Successfully extracted battle data from {len(all_battles_data)} out of {len(battle_urls)} battles")

        if all_battles_data:
            # Calculate and save averages to a single Excel file (default name 'battle_stats_averages.xlsx')
            averages_data = calculate_averages(all_battles_data)
            save_averages_to_excel(averages_data)
            logger.info("All battles processed successfully")
        else:
            logger.error("No battle data was extracted from any battle")
            
    finally:
        driver.quit()
        logger.info("Browser closed")

if __name__ == "__main__":
    main() 