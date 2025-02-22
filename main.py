from flask import Flask, render_template, request, jsonify
from src.services.video_service import VideoService
from src.config.setup import Settings
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv() 

app = Flask(__name__)
settings = Settings()
video_service = VideoService(settings)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    try:
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            return jsonify({'error': 'No URL provided'}), 400

        result = video_service.process_youtube_video(youtube_url)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)