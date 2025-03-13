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
    logger.info("Setting up Chrome driver...")
    chrome_options = Options()
    
    # Enable headless mode and other required options
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    try:
        # Try to find Chrome binary
        chrome_binary = None
        chrome_dir = os.getenv('CHROME_DIR', '/opt/render/project/src/chrome')
        logger.info(f"Looking for Chrome in: {chrome_dir}")
        
        # Check if Chrome is installed
        chrome_installed = os.path.exists(os.path.join(chrome_dir, '.chrome_installed'))
        logger.info(f"Chrome installation marker exists: {chrome_installed}")
        
        # List directory contents
        try:
            logger.info(f"Contents of {chrome_dir}:")
            for item in os.listdir(chrome_dir):
                item_path = os.path.join(chrome_dir, item)
                logger.info(f"  {item}: {os.path.getsize(item_path)} bytes")
        except Exception as e:
            logger.error(f"Failed to list chrome directory contents: {str(e)}")
        
        # Try possible Chrome binary paths
        possible_paths = [
            '/usr/bin/google-chrome-stable',  # System installation
            '/usr/bin/google-chrome',         # System symlink
            os.path.join(chrome_dir, 'google-chrome-stable'),
            os.path.join(chrome_dir, 'google-chrome'),
        ]
        
        # Try possible paths
        for path in possible_paths:
            logger.info(f"Checking Chrome binary at: {path}")
            if os.path.exists(path):
                if os.path.islink(path):
                    real_path = os.path.realpath(path)
                    logger.info(f"Path {path} is a symlink to {real_path}")
                chrome_binary = path
                logger.info(f"Found Chrome at: {chrome_binary}")
                # Check if the file is executable
                if os.access(path, os.X_OK):
                    logger.info(f"Chrome binary is executable")
                else:
                    logger.warning(f"Chrome binary is not executable, attempting to make it executable")
                    try:
                        os.chmod(path, 0o755)
                        logger.info("Successfully made Chrome binary executable")
                    except Exception as e:
                        logger.error(f"Failed to make Chrome binary executable: {str(e)}")
                break
            else:
                logger.info(f"Chrome not found at: {path}")
        
        if not chrome_binary:
            # Try to find Chrome using which command
            try:
                import subprocess
                chrome_binary = subprocess.check_output(['which', 'google-chrome-stable']).decode().strip()
                logger.info(f"Found Chrome using which command: {chrome_binary}")
            except Exception as e:
                logger.error(f"Failed to find Chrome using which command: {str(e)}")
                raise FileNotFoundError("Chrome binary not found in any known location")
            
        # Set up ChromeDriver
        chromedriver_path = os.path.join(chrome_dir, 'chromedriver')
        if not os.path.exists(chromedriver_path):
            logger.error(f"ChromeDriver not found at {chromedriver_path}")
            raise FileNotFoundError(f"ChromeDriver not found at {chromedriver_path}")
        
        # Log Chrome and ChromeDriver versions
        try:
            chrome_version = subprocess.check_output([chrome_binary, '--version', '--no-sandbox']).decode().strip()
            chromedriver_version = subprocess.check_output([chromedriver_path, '--version']).decode().strip()
            logger.info(f"Chrome version: {chrome_version}")
            logger.info(f"ChromeDriver version: {chromedriver_version}")
        except Exception as e:
            logger.warning(f"Could not get version information: {str(e)}")
        
        # Add Chrome binary directory to PATH
        chrome_bin_dir = os.path.dirname(chrome_binary)
        os.environ['PATH'] = f"{chrome_bin_dir}:{chrome_dir}:{os.environ.get('PATH', '')}"
        logger.info(f"Updated PATH with Chrome directories: {chrome_bin_dir}, {chrome_dir}")
        
        chrome_options.binary_location = chrome_binary
        service = Service(executable_path=chromedriver_path)
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        logger.info("Chrome driver setup successful")
        return driver
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {str(e)}")
        raise

def extract_battle_data(driver, battle_url):
    logger.info(f"Accessing battle page: {battle_url}")
    try:
        driver.get(battle_url)
        
        # Wait for page to load
        logger.info("Waiting for page to load...")
        time.sleep(15)
        
        # Try to find the battle result div using XPath to find div with result attribute
        result_selectors = [
            "//div[@result='win']",  # Look for victory
            "//div[@result='loss']"  # Look for defeat
        ]
        
        is_victory = None
        for selector in result_selectors:
            try:
                logger.info(f"Trying to find result div with selector: {selector}")
                elements = driver.find_elements(By.XPATH, selector)
                
                if elements:
                    logger.info(f"Found {len(elements)} result elements with selector {selector}")
                    is_victory = 'win' in selector
                    logger.info(f"Battle result: {'Victory' if is_victory else 'Defeat'}")
                    break
            except Exception as e:
                logger.warning(f"Failed with result selector {selector}: {str(e)}")
                continue
        
        if is_victory is None:
            logger.warning("Could not find result div element")
            return None, []
        
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
            return None, []
        
        # Get all rows
        rows = table.find_elements(By.TAG_NAME, "tr")
        logger.info(f"Found {len(rows)} total rows")
        
        if len(rows) <= 1:
            logger.error("Not enough rows found in table")
            return None, []
        
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
            return None, []
        else:
            logger.info(f"Successfully extracted data from {len(battle_data)} rows")
        
        return is_victory, battle_data
    
    except Exception as e:
        logger.error(f"Error accessing battle page: {str(e)}")
        return None, []

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
            
            # Process accuracy (format: "shots/hits/pens")
            try:
                shots, hits, pens = map(int, player['Accuracy'].split('/'))
                player_stats[name]['accuracy_shots'] += shots
                player_stats[name]['accuracy_hits'] += hits
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
                # Calculate hit rate (hits / shots)
                hit_rate = (stats['accuracy_hits'] / stats['accuracy_shots']) * 100
                # Calculate pen rate (pens / hits)
                pen_rate = (stats['accuracy_pens'] / stats['accuracy_hits']) * 100 if stats['accuracy_hits'] > 0 else 0
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

def save_averages_to_excel(averages_data, output_file, battle_summary=None):
    """Save averages data to Excel file with optional battle summary."""
    if not averages_data:
        logger.warning("No average data to save")
        return

    try:
        # Create DataFrame and sort by Avg Damage in descending order
        df = pd.DataFrame(averages_data)
        df = df.sort_values(by='Avg Damage', ascending=False)
        
        # Modify Tank List to be more compact
        df['Tank List'] = df['Tank List'].apply(lambda x: x.replace(', ', ','))
        
        # Create Excel writer object with xlsxwriter engine
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        
        # Write averages data
        df.to_excel(writer, sheet_name='Player Averages', index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Player Averages']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B5320',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': False  # Disable text wrapping for tank list
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0.0'
        })
        
        # Set column widths
        column_widths = {
            'Name': 30,
            'Battles': 10,
            'Avg Damage': 12,
            'Avg Frags': 10,
            'Avg Assist': 12,
            'Avg Spots': 10,
            'Avg XP': 10,
            'Tanks Used': 12,
            'Tank List': 35,  # Fixed width for tank list
            'Hit Rate': 10,
            'Pen Rate': 10,
            'Avg Survival': 12
        }
        
        # Set fixed column widths
        for col_num, column in enumerate(df.columns):
            width = column_widths.get(column, 15)
            worksheet.set_column(col_num, col_num, width)
        
        # Format headers
        for col_num, column in enumerate(df.columns):
            worksheet.write(0, col_num, column, header_format)
        
        # Write data with formatting
        for row in range(len(df)):
            for col, column in enumerate(df.columns):
                value = df.iloc[row][column]
                if column == 'Tank List':
                    # Add a comment with the full tank list
                    full_list = str(value).replace(',', '\n')
                    worksheet.write_comment(row + 1, col, full_list, {'width': 200, 'height': 100})
                    # Write the truncated value
                    if len(str(value)) > 50:
                        truncated = str(value)[:47] + "..."
                        worksheet.write(row + 1, col, truncated, cell_format)
                    else:
                        worksheet.write(row + 1, col, value, cell_format)
                elif isinstance(value, (int, float)) and column not in ['Battles', 'Tanks Used']:
                    worksheet.write_number(row + 1, col, value, number_format)
                else:
                    worksheet.write(row + 1, col, value, cell_format)
        
        # Set row height
        worksheet.set_default_row(20)
        
        # Add alternating row colors
        for row in range(1, len(df) + 1, 2):
            worksheet.set_row(row, None, workbook.add_format({
                'bg_color': '#F0F0F0',
                'border': 1,
                'text_wrap': False,
                'valign': 'vcenter'
            }))
        
        # Add battle summary below the main table if provided
        if battle_summary:
            summary_start_row = len(df) + 3
            summary_format = workbook.add_format({
                'bold': True,
                'align': 'left',
                'valign': 'vcenter',
                'font_size': 11
            })
            
            summary_text = (
                f"Battle Summary - "
                f"Total Battles: {battle_summary['total_battles']}  |  "
                f"Victories: {battle_summary['victories']}  |  "
                f"Defeats: {battle_summary['defeats']}  |  "
                f"Win Rate: {battle_summary['win_rate']:.1f}%"
            )
            
            worksheet.merge_range(
                summary_start_row, 0, 
                summary_start_row, len(df.columns) - 1, 
                summary_text, summary_format
            )
        
        writer.close()
        logger.info(f"Excel file saved successfully to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error saving Excel file: {str(e)}")
        raise

def main():
    # List of battle URLs to process (reduced to 5 for testing)
    battle_urls = [
        "https://tomato.gg/battle/69523015319287012/512317641",
        "https://tomato.gg/battle/81469217745007248/512317641",
        "https://tomato.gg/battle/69522414023864650/512317641",
        "https://tomato.gg/battle/69521885742886864/512317641",
        "https://tomato.gg/battle/66958537591484033/512317641",
        "https://tomato.gg/battle/81469050241281261/512317641",
        "https://tomato.gg/battle/72222543998741235/512317641",
        "https://tomato.gg/battle/76679624835328412/512317641",
        "https://tomato.gg/battle/76679740799445025/512317641",
        "https://tomato.gg/battle/66003611742758354/512317641",
        "https://tomato.gg/battle/66958322843116718/512317641",
        "https://tomato.gg/battle/76680123051533203/512317641",
        "https://tomato.gg/battle/69522607297389211/512317641",
        "https://tomato.gg/battle/67896068822655321/512317641",
        "https://tomato.gg/battle/72223360042524692/512317641",
        "https://tomato.gg/battle/66958464577036084/512317641",
        "https://tomato.gg/battle/66958120979652186/512317641",
        "https://tomato.gg/battle/72224107366833189/512317641",
        "https://tomato.gg/battle/69522701786667730/512317641",
        "https://tomato.gg/battle/64391779236043210/512317641"
    ]
    
    driver = setup_driver()
    all_battles_data = []
    global victories, defeats
    victories = 0
    defeats = 0
    
    try:
        # Process each battle URL
        for i, url in enumerate(battle_urls, 1):
            logger.info(f"\nProcessing battle {i} of {len(battle_urls)}")
            is_victory, battle_data = extract_battle_data(driver, url)
            if battle_data:
                all_battles_data.append(battle_data)
                if is_victory is not None:
                    if is_victory:
                        victories += 1
                    else:
                        defeats += 1
            
        logger.info(f"Successfully extracted battle data from {len(all_battles_data)} out of {len(battle_urls)} battles")
        logger.info(f"Total Victories: {victories}, Total Defeats: {defeats}")

        if all_battles_data:
            # Calculate and save averages to a single Excel file named "day 3.xlsx"
            averages_data = calculate_averages(all_battles_data)
            battle_summary = {
                'total_battles': len(all_battles_data),
                'victories': victories,
                'defeats': defeats,
                'win_rate': (victories / (victories + defeats) * 100) if victories + defeats > 0 else 0
            }
            save_averages_to_excel(averages_data, "day 3.xlsx", battle_summary)
            logger.info("All battles processed successfully")
        else:
            logger.error("No battle data was extracted from any battle")
            
    finally:
        driver.quit()
        logger.info("Browser closed")

if __name__ == "__main__":
    main()