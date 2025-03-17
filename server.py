import os
import requests
from flask import Flask, jsonify, request, send_from_directory, Response
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
        status_messages.append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 100 messages
        if len(status_messages) > 100:
            status_messages.pop(0)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Serve static audio files
@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(os.path.join(app.static_folder, 'audio'), filename)

@app.route('/api/urls', methods=['GET'])
def get_urls():
    return jsonify(storage.get_urls())

@app.route('/api/urls', methods=['POST'])
def add_url():
    url = request.json.get('url')
    if storage.add_url(url):
        return jsonify({"success": True, "message": "URL added successfully"})
    return jsonify({
        "success": False,
        "message": "Invalid URL or already exists"
    })

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
        "newsletter_time": storage.get_setting("newsletter_time"),
        "create_podcast": storage.get_setting("create_podcast", "false"),
        "podcast_studio_prompt": storage.get_setting("podcast_studio_prompt", "")
    })

@app.route('/api/settings', methods=['POST'])
def save_settings():
    settings = request.json
    for key, value in settings.items():
        storage.save_setting(key, str(value))

    # Restart scheduler with new settings
    newsletter_time = settings.get('newsletter_time', '08:00')
    start_scheduler(newsletter_time)

    return jsonify({"success": True})

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Using "Rachel" voice

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    try:
        podcast_index = request.json.get('podcast_index')
        print(f"Generating audio for podcast index: {podcast_index}")

        # Get the most recent newsletter with a podcast script
        newsletters = storage.get_newsletters()
        podcasts = [n for n in newsletters if n.get('podcast_script')]

        print(f"Found {len(podcasts)} podcasts with scripts")

        if podcast_index >= len(podcasts):
            print(f"Podcast index {podcast_index} out of range")
            return jsonify({"error": "Podcast not found"}), 404

        podcast = podcasts[podcast_index]['podcast_script']['podcast']
        print(f"Processing podcast: {podcast['title']}")

        # Generate audio for each line of dialog
        audio_parts = []
        for i, line in enumerate(podcast['dialog']):
            print(f"Generating audio for line {i+1}/{len(podcast['dialog'])}")
            try:
                response = requests.post(
                    ELEVENLABS_API_URL,
                    headers={
                        'xi-api-key': ELEVENLABS_API_KEY,
                        'Content-Type': 'application/json'
                    },
                    json={
                        'text': line['text'],
                        'model_id': 'eleven_multilingual_v2',
                        'voice_settings': {
                            'stability': 0.5,
                            'similarity_boost': 0.5
                        }
                    },
                    stream=True
                )

                print(f"Elevenlabs API response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"API Error response: {response.text}")
                    return jsonify({"error": f"Failed to generate audio: {response.text}"}), 500

                audio_parts.append(response.content)
            except Exception as e:
                print(f"Error generating audio for line {i+1}: {str(e)}")
                return jsonify({"error": f"Error generating audio for line {i+1}: {str(e)}"}), 500

        # Save the audio file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_filename = f'podcast_{timestamp}.mp3'
        audio_path = os.path.join(app.static_folder, 'audio', audio_filename)

        # Ensure audio directory exists
        try:
            os.makedirs(os.path.join(app.static_folder, 'audio'), exist_ok=True)
            print(f"Created audio directory at {os.path.join(app.static_folder, 'audio')}")
        except Exception as e:
            print(f"Error creating audio directory: {str(e)}")
            return jsonify({"error": f"Failed to create audio directory: {str(e)}"}), 500

        try:
            with open(audio_path, 'wb') as f:
                f.write(audio_parts[0])
            print(f"Saved audio file to {audio_path}")
        except Exception as e:
            print(f"Error saving audio file: {str(e)}")
            return jsonify({"error": f"Failed to save audio file: {str(e)}"}), 500

        return jsonify({
            "success": True,
            "audio_url": f'/static/audio/{audio_filename}'
        })

    except Exception as e:
        print(f"Unexpected error in generate_audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start scheduler with initial settings
    newsletter_time = storage.get_setting("newsletter_time", "08:00")
    start_scheduler(newsletter_time)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000)