# Tomato.gg Web Scraper

A Python tool to scrape player game data from [tomato.gg](https://tomato.gg), a World of Tanks statistics website.

## Setup

1. Make sure you have Python 3.8+ installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Edit the `tomato_scraper.py` file to add the player names you want to scrape in the `player_names` list
2. Run the script:
   ```
   python tomato_scraper.py
   ```
3. The scraped data will be saved in the `data` directory as CSV files

## Important Notes

- The current script contains placeholder selectors. You'll need to inspect the actual HTML structure of tomato.gg and update the selectors in the `extract_player_stats` and `extract_recent_battles` functions.
- Be respectful of the website's resources. Add appropriate delays between requests and don't overload their servers.
- Check the website's Terms of Service to ensure web scraping is allowed.

## Advanced Usage

### Using Selenium for Dynamic Content

If some data on tomato.gg is loaded dynamically with JavaScript, you might need to use Selenium instead of requests/BeautifulSoup. An example implementation is provided in `selenium_scraper.py`.

### Proxy Rotation

For large-scale scraping, consider implementing proxy rotation to avoid IP bans.

## License

This project is for educational purposes only. 