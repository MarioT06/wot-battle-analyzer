# WoT Battle Stats Analyzer

A web application that analyzes World of Tanks battle statistics from tomato.gg URLs.

## Features

- Process multiple battle URLs simultaneously
- Display individual battle statistics
- Calculate and display average stats across all battles
- Export statistics to Excel files
- Interactive web interface with sorting and filtering
- Tank list display with hover functionality
- Progress tracking during battle processing

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

3. Paste your battle URLs (one per line) into the text area
4. Click "Process Battles"
5. View individual battle stats and averages in the tabs
6. Download Excel reports using the provided buttons

## Project Structure

- `app.py` - Flask application and routes
- `battle_scraper.py` - Battle data scraping and processing logic
- `templates/index.html` - Web interface template
- `requirements.txt` - Python dependencies
- `analyses/` - Directory for generated Excel files

## Dependencies

- Python 3.8+
- Flask
- Selenium
- pandas
- xlsxwriter
- Socket.IO

## Notes

- The application uses Chrome WebDriver for scraping
- Make sure Chrome is installed on your system
- Excel files are saved in the `analyses` directory 