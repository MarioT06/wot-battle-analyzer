from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import pandas as pd
import time
import logging
import os
from collections import defaultdict
import concurrent.futures
import random
from concurrent.futures import ThreadPoolExecutor
import queue
from contextlib import contextmanager
import urllib3

# Configure urllib3 connection pooling
urllib3.PoolManager(maxsize=10, retries=3)

# Set up logging - reduce logging to speed up processing
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Disable Selenium logging
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.WARNING)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.WARNING)

# Global rate limiting queue - increased limit for faster processing
request_queue = queue.Queue()
MAX_REQUESTS_PER_MINUTE = 60
DELAY_BETWEEN_REQUESTS = 60 / MAX_REQUESTS_PER_MINUTE
MAX_RETRIES = 3
RETRY_DELAY = 5

@contextmanager
def create_driver():
    """Context manager for creating and properly closing Chrome driver"""
    driver = None
    try:
        driver = setup_driver()
        yield driver
    except Exception as e:
        logger.error(f"Error in create_driver: {str(e)}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def rate_limit():
    """Implement rate limiting for requests"""
    try:
        current_time = time.time()
        request_queue.put_nowait(current_time)
        if request_queue.qsize() > MAX_REQUESTS_PER_MINUTE:
            oldest_request = request_queue.get()
            time_since_oldest = current_time - oldest_request
            if time_since_oldest < 60:
                time.sleep(max(0.1, (60 - time_since_oldest) / MAX_REQUESTS_PER_MINUTE))
    except queue.Full:
        time.sleep(DELAY_BETWEEN_REQUESTS)

def setup_driver():
    """Set up Chrome driver with optimized settings"""
    # Try different ports if the default one is in use
    ports = list(range(9515, 9525))  # Try ports 9515-9524
    random.shuffle(ports)  # Randomize to avoid conflicts
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-dev-tools')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dbus')
    chrome_options.add_argument('--no-zygote')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--disable-features=TranslateUI')
    chrome_options.add_argument('--remote-debugging-port=0')  # Use random debugging port
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--disable-translate')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--metrics-recording-only')
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--no-default-browser-check')
    chrome_options.add_argument('--force-webrtc-ip-handling-policy=disable_non_proxied_udp')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-breakpad')
    chrome_options.add_argument('--disable-component-extensions-with-background-pages')
    chrome_options.add_argument('--disable-features=BackForwardCache')
    chrome_options.add_argument('--disable-ipc-flooding-protection')
    chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    chrome_options.add_experimental_option('detach', True)
    
    last_exception = None
    for port in ports:
        try:
            # Log environment information only once at startup
            if port == ports[0]:
                logger.warning(f"Current working directory: {os.getcwd()}")
                logger.warning(f"PATH: {os.environ.get('PATH', '')}")
                logger.warning(f"Chrome directory: {os.getenv('CHROME_DIR', '/opt/render/project/src/chrome')}")
            
            chrome_dir = os.getenv('CHROME_DIR', '/opt/render/project/src/chrome')
            possible_paths = [
                os.path.join(chrome_dir, name) for name in 
                ['chrome', 'google-chrome', 'google-chrome-stable']
            ]
            
            # Log Chrome binary information only once
            if port == ports[0]:
                for path in possible_paths:
                    if os.path.exists(path):
                        logger.warning(f"Found Chrome binary at: {path}")
                        logger.warning(f"Chrome binary permissions: {oct(os.stat(path).st_mode)[-3:]}")
            
            chrome_binary = next(
                (path for path in possible_paths if os.path.exists(path)), 
                None
            )
            
            if not chrome_binary:
                raise FileNotFoundError("Chrome binary not found")
            
            chromedriver_path = os.path.join(chrome_dir, 'chromedriver')
            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError("ChromeDriver not found")
            
            # Log ChromeDriver permissions only once
            if port == ports[0]:
                logger.warning(f"ChromeDriver permissions: {oct(os.stat(chromedriver_path).st_mode)[-3:]}")
            
            # Ensure proper PATH setup
            os.environ['PATH'] = f"{chrome_dir}:{os.environ.get('PATH', '')}"
            chrome_options.binary_location = chrome_binary
            
            # Create service with specific port and log settings
            service = Service(
                executable_path=chromedriver_path,
                port=port,
                log_output=os.devnull
            )
            
            # Create and configure driver with increased timeouts
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.command_executor.set_timeout(30)
            
            # Test the connection
            driver.execute_script('return navigator.userAgent')
            logger.warning(f"Successfully connected to ChromeDriver on port {port}")
            return driver
            
        except Exception as e:
            last_exception = e
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
            
    raise Exception(f"Failed to create Chrome driver on any port. Last error: {str(last_exception)}")

def extract_battle_data_with_retry(driver, battle_url, max_retries=MAX_RETRIES):
    """Extract battle data with retry logic"""
    for attempt in range(max_retries):
        try:
            rate_limit()
            
            # Log attempt information
            logger.warning(f"Processing battle {battle_url} (Attempt {attempt + 1}/{max_retries})")
            
            # Clear any existing state
            try:
                driver.delete_all_cookies()
                driver.execute_script("window.localStorage.clear();")
                driver.execute_script("window.sessionStorage.clear();")
            except Exception as e:
                logger.warning(f"Failed to clear browser state: {str(e)}")
            
            # Test driver health before proceeding
            try:
                driver.current_url
            except Exception as e:
                logger.warning(f"Driver health check failed: {str(e)}")
                raise WebDriverException("Driver is not responsive")
            
            # Load the page with retry on timeout
            load_attempts = 3
            for load_attempt in range(load_attempts):
                try:
                    logger.warning(f"Loading page (Attempt {load_attempt + 1}/{load_attempts})")
                    driver.get(battle_url)
                    break
                except TimeoutException:
                    if load_attempt < load_attempts - 1:
                        logger.warning(f"Page load timeout, attempt {load_attempt + 1}/{load_attempts}")
                        continue
                    raise
                except Exception as e:
                    logger.warning(f"Unexpected error during page load: {str(e)}")
                    raise
            
            # Wait for result element with a more robust check
            wait = WebDriverWait(driver, 30)  # Increased timeout
            result_xpath = "//div[@result='win'] | //div[@result='loss']"
            
            # First check if page loaded at all
            try:
                body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.warning("Page body loaded successfully")
            except TimeoutException:
                logger.warning("Timeout waiting for page body")
                raise
            
            # Check for error indicators
            try:
                if "404" in driver.title or "Error" in driver.title:
                    logger.warning(f"Error page detected: {driver.title}")
                    return None, []
                if "404" in driver.page_source or "error" in driver.page_source.lower():
                    logger.warning("Error content detected in page source")
                    return None, []
            except Exception as e:
                logger.warning(f"Error checking page content: {str(e)}")
            
            # Then check for specific elements
            try:
                result_element = wait.until(EC.presence_of_element_located((By.XPATH, result_xpath)))
                logger.warning("Battle result element found")
            except TimeoutException:
                logger.warning("Timeout waiting for battle result element")
                if "404" in driver.title or "Error" in driver.title:
                    logger.warning(f"Battle page not found or error: {battle_url}")
                    return None, []
                raise
            
            is_victory = 'win' in result_element.get_attribute('result')
            logger.warning(f"Battle result: {'Victory' if is_victory else 'Defeat'}")
            
            # Wait for table with explicit presence check
            try:
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                if not table.is_displayed():
                    wait.until(EC.visibility_of(table))
                logger.warning("Battle data table found and visible")
            except TimeoutException:
                logger.warning("Timeout waiting for battle data table")
                raise
            
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            logger.warning(f"Found {len(rows)} player rows in table")
            
            battle_data = []
            for row_index, row in enumerate(rows, 1):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 10:
                        logger.warning(f"Row {row_index} has insufficient cells: {len(cells)}")
                        continue
                    
                    stats = {
                        'Name': cells[2].text.strip(),
                        'Tank': cells[1].text.strip(),
                        'Damage': ''.join(filter(str.isdigit, cells[3].text.strip())) or '0',
                        'Frags': ''.join(filter(str.isdigit, cells[4].text.strip())) or '0',
                        'Assist': ''.join(filter(str.isdigit, cells[5].text.strip())) or '0',
                        'Spots': ''.join(filter(str.isdigit, cells[6].text.strip())) or '0',
                        'Accuracy': cells[7].text.strip(),
                        'Survival': cells[8].text.strip(),
                        'XP': ''.join(filter(str.isdigit, cells[9].text.strip())) or '0'
                    }
                    
                    if stats['Name'] and stats['Tank']:
                        battle_data.append(stats)
                        logger.warning(f"Processed player: {stats['Name']} in {stats['Tank']}")
                    else:
                        logger.warning(f"Row {row_index} missing required data: Name={bool(stats['Name'])}, Tank={bool(stats['Tank'])}")
                    
                except Exception as e:
                    logger.warning(f"Error processing row {row_index}: {str(e)}")
                    continue
            
            if battle_data:  # Only return if we got data
                logger.warning(f"Successfully extracted data for {len(battle_data)} players")
                return is_victory, battle_data
            else:
                logger.warning("No valid battle data found in table")
                raise Exception("No valid battle data found in table")
            
        except (WebDriverException, TimeoutException) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed for {battle_url}: {str(e)}")
                time.sleep(RETRY_DELAY)  # Wait before retrying
                try:
                    # Try to recover the driver
                    driver.execute_script('return navigator.userAgent')
                    logger.warning("Driver recovery successful")
                except Exception as recovery_e:
                    logger.warning(f"Driver recovery failed: {str(recovery_e)}")
                    # If driver is dead, create a new one
                    try:
                        driver.quit()
                    except:
                        pass
                    logger.warning("Creating new driver instance")
                    driver = setup_driver()
            else:
                logger.error(f"All attempts failed for {battle_url}: {str(e)}")
                return None, []
        except Exception as e:
            logger.error(f"Unexpected error processing {battle_url}: {str(e)}")
            return None, []
    
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

def process_battle_chunk(battle_urls_chunk):
    """Process a chunk of battle URLs with a single Chrome instance"""
    chunk_data = []
    chunk_victories = 0
    chunk_defeats = 0
    
    with create_driver() as driver:
        for url in battle_urls_chunk:
            is_victory, battle_data = extract_battle_data_with_retry(driver, url)
            if battle_data:
                chunk_data.append(battle_data)
                if is_victory is not None:
                    if is_victory:
                        chunk_victories += 1
                    else:
                        chunk_defeats += 1
    
    return chunk_data, chunk_victories, chunk_defeats

def main():
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
    
    # Use single thread for maximum stability
    max_threads = 1  # Process battles sequentially
    chunk_size = len(battle_urls)  # Process all battles in one chunk
    url_chunks = [battle_urls]  # Single chunk containing all URLs
    
    all_battles_data = []
    total_victories = 0
    total_defeats = 0
    processed_battles = 0
    failed_battles = []  # Track failed battles
    
    start_time = time.time()
    logger.warning(f"Starting battle processing in single-threaded mode")
    
    try:
        # Process all battles in a single chunk
        with create_driver() as driver:
            for url in battle_urls:
                try:
                    is_victory, battle_data = extract_battle_data_with_retry(driver, url)
                    if battle_data:
                        all_battles_data.append(battle_data)
                        if is_victory is not None:
                            if is_victory:
                                total_victories += 1
                            else:
                                total_defeats += 1
                        processed_battles += 1
                        
                        # Show progress
                        elapsed_time = time.time() - start_time
                        battles_per_second = processed_battles / elapsed_time if elapsed_time > 0 else 0
                        logger.warning(f"Processed {processed_battles}/{len(battle_urls)} battles. "
                                     f"Speed: {battles_per_second:.2f} battles/second")
                    else:
                        failed_battles.append(url)
                        logger.error(f"Failed to process battle: {url}")
                        
                except Exception as e:
                    failed_battles.append(url)
                    logger.error(f"Error processing battle {url}: {str(e)}")
                    continue
    
    except Exception as e:
        logger.error(f"Critical error during processing: {str(e)}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Log detailed summary
    logger.warning("\nProcessing Summary:")
    logger.warning(f"Total time: {processing_time:.2f} seconds")
    logger.warning(f"Successfully processed: {processed_battles}/{len(battle_urls)} battles")
    logger.warning(f"Average speed: {processed_battles/processing_time:.2f} battles/second")
    logger.warning(f"Victories: {total_victories}")
    logger.warning(f"Defeats: {total_defeats}")
    
    if failed_battles:
        logger.warning("\nFailed Battles:")
        for url in failed_battles:
            logger.warning(f"- {url}")
    
    if all_battles_data:
        averages_data = calculate_averages(all_battles_data)
        battle_summary = {
            'total_battles': len(all_battles_data),
            'victories': total_victories,
            'defeats': total_defeats,
            'win_rate': (total_victories / (total_victories + total_defeats) * 100) if total_victories + total_defeats > 0 else 0
        }
        
        try:
            save_averages_to_excel(averages_data, "day 3.xlsx", battle_summary)
            logger.warning("\nResults saved to Excel file")
        except Exception as e:
            logger.error(f"Error saving to Excel: {str(e)}")
            # Attempt to save as CSV as fallback
            try:
                csv_path = "day 3.csv"
                pd.DataFrame(averages_data).to_csv(csv_path, index=False)
                logger.warning(f"Results saved to CSV file: {csv_path}")
            except Exception as e2:
                logger.error(f"Error saving to CSV: {str(e2)}")
    else:
        logger.error("No battle data was extracted")

if __name__ == "__main__":
    main()