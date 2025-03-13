from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from battle_scraper import setup_driver, extract_battle_data_with_retry, calculate_averages, save_averages_to_excel, create_driver
import threading
import queue
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# Queue for processing battles
battle_queue = queue.Queue()

# Store for analyses
ANALYSES_DIR = 'analyses'
if not os.path.exists(ANALYSES_DIR):
    os.makedirs(ANALYSES_DIR)

@app.route('/')
def index():
    logger.info("Accessing index page")
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_battles():
    urls = request.json.get('urls', [])
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    # Start processing in background
    thread = threading.Thread(target=process_battle_urls, args=(urls,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Processing started'})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(ANALYSES_DIR, filename)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/download_averages/<filename>')
def download_averages(filename):
    try:
        # The file is already saved with the correct name, no need to modify it
        file_path = os.path.join(ANALYSES_DIR, filename)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/previous_analyses')
def get_previous_analyses():
    analyses = []
    for filename in os.listdir(ANALYSES_DIR):
        if filename.endswith('.xlsx'):
            file_path = os.path.join(ANALYSES_DIR, filename)
            analyses.append({
                'filename': filename,
                'date': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': os.path.getsize(file_path)
            })
    return jsonify(analyses)

def process_battle_urls(urls):
    logger.info(f"Starting to process {len(urls)} battle URLs")
    all_battles_data = []
    victories = 0
    defeats = 0
    
    try:
        with create_driver() as driver:
            logger.info("WebDriver setup complete")
            
            total_battles = len(urls)
            for i, url in enumerate(urls, 1):
                try:
                    # Emit progress update
                    progress = (i / total_battles) * 100
                    logger.info(f"Processing battle {i}/{total_battles}: {url}")
                    socketio.emit('progress', {
                        'current': i,
                        'total': total_battles,
                        'percentage': progress,
                        'url': url
                    }, namespace='/')
                    
                    is_victory, battle_data = extract_battle_data_with_retry(driver, url)
                    if battle_data:
                        all_battles_data.append(battle_data)
                        if is_victory is not None:
                            if is_victory:
                                victories += 1
                            else:
                                defeats += 1
                        
                        # Emit battle result with full stats
                        logger.info(f"Battle {i} processed successfully")
                        socketio.emit('battle_processed', {
                            'url': url,
                            'result': 'Victory' if is_victory else 'Defeat' if is_victory is not None else 'Unknown',
                            'stats': battle_data
                        }, namespace='/')
                    else:
                        logger.warning(f"No data extracted for battle {i}: {url}")
                        socketio.emit('battle_processed', {
                            'url': url,
                            'result': 'Unknown',
                            'stats': []
                        }, namespace='/')
                    
                except Exception as e:
                    logger.error(f"Error processing battle {i}: {str(e)}")
                    socketio.emit('battle_processed', {
                        'url': url,
                        'result': 'Error',
                        'stats': []
                    }, namespace='/')
            
            if all_battles_data:
                logger.info("Processing complete, calculating averages")
                # Calculate averages
                averages_data = calculate_averages(all_battles_data)
                
                # Add battle summary to averages data
                battle_summary = {
                    'victories': victories,
                    'defeats': defeats,
                    'total_battles': len(all_battles_data),
                    'win_rate': (victories / (victories + defeats) * 100) if victories + defeats > 0 else 0
                }
                
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                excel_filename = f"battle_stats_{timestamp}.xlsx"
                excel_path = os.path.join(ANALYSES_DIR, excel_filename)
                
                # Save averages Excel file with battle summary
                logger.info(f"Saving averages to {excel_path}")
                save_averages_to_excel(averages_data, excel_path, battle_summary)
                
                # Emit final results with averages
                logger.info("Emitting final results")
                socketio.emit('processing_complete', {
                    'victories': victories,
                    'defeats': defeats,
                    'total_battles': len(all_battles_data),
                    'win_rate': (victories / (victories + defeats) * 100) if victories + defeats > 0 else 0,
                    'averages': averages_data,
                    'excel_file': excel_filename  # This is now the correct filename
                }, namespace='/')
            else:
                logger.error("No battle data was extracted from any battle")
                socketio.emit('processing_error', {
                    'message': 'No battle data was extracted from any battle'
                }, namespace='/')
            
    except Exception as e:
        logger.error(f"Error processing battles: {str(e)}")
        socketio.emit('processing_error', {
            'message': f'Error processing battles: {str(e)}'
        }, namespace='/')

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting application on port {port}")
    socketio.run(app, 
                host='0.0.0.0', 
                port=port,
                debug=False,
                use_reloader=False,
                log_output=True) 