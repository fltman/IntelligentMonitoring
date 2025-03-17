from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from utils.storage import Storage
from utils.article_processor import ArticleProcessor
from utils.newsletter import NewsletterGenerator
from utils.scheduler import start_scheduler, process_urls, generate_daily_newsletter
import threading
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize components
storage = Storage()
processor = ArticleProcessor()

# Queue for status messages
status_messages = []
status_lock = threading.Lock()

def add_status_message(message):
    with status_lock:
        status_messages.append({"message": message, "timestamp": datetime.now().isoformat()})
        # Keep only last 100 messages
        if len(status_messages) > 100:
            status_messages.pop(0)

# Serve static files
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/urls', methods=['GET'])
def get_urls():
    return jsonify(storage.get_urls())

@app.route('/api/urls', methods=['POST'])
def add_url():
    url = request.json.get('url')
    if storage.add_url(url):
        return jsonify({"success": True, "message": "URL added successfully"})
    return jsonify({"success": False, "message": "Invalid URL or already exists"})

@app.route('/api/urls/<path:url>', methods=['DELETE'])
def remove_url(url):
    storage.remove_url(url)
    return jsonify({"success": True})

@app.route('/api/articles', methods=['GET'])
def get_articles():
    return jsonify(storage.get_recent_articles())

@app.route('/api/newsletters', methods=['GET'])
def get_newsletters():
    search = request.args.get('search', '')
    return jsonify(storage.get_newsletters(search if search else None))

@app.route('/api/status', methods=['GET'])
def get_status():
    with status_lock:
        return jsonify(status_messages)

@app.route('/api/process', methods=['POST'])
def start_processing():
    def status_callback(message):
        add_status_message(message)

    # Start processing in a background thread
    thread = threading.Thread(target=process_urls, args=(status_callback,))
    thread.daemon = True
    thread.start()

    return jsonify({"success": True, "message": "Processing started"})

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({
        "interest_prompt": storage.get_setting("interest_prompt"),
        "summary_prompt": storage.get_setting("summary_prompt"),
        "newsletter_template": storage.get_setting("newsletter_template"),
        "url_check_interval": storage.get_setting("url_check_interval"),
        "newsletter_time": storage.get_setting("newsletter_time")
    })

@app.route('/api/settings', methods=['POST'])
def save_settings():
    settings = request.json
    for key, value in settings.items():
        storage.save_setting(key, str(value))

    # Restart scheduler with new settings
    start_scheduler(
        int(settings.get('url_check_interval', 1)),
        settings.get('newsletter_time', '08:00')
    )

    return jsonify({"success": True})

if __name__ == '__main__':
    # Start scheduler with initial settings
    url_check_interval = int(storage.get_setting("url_check_interval", "1"))
    newsletter_time = storage.get_setting("newsletter_time", "08:00")
    start_scheduler(url_check_interval, newsletter_time)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000)