# app.py - Web Sunucusu
from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Sonuçların okunacağı yol.
DATA_PATH = os.environ.get('DATA_PATH', '.')
RESULTS_FILE = os.path.join(DATA_PATH, 'results.json')

@app.route('/')
def dashboard():
    # Bu sayfa artık sadece dashboard.html'i gösterir.
    return render_template('dashboard.html')

@app.route('/get_analysis_data')
def get_analysis_data():
    """JSON dosyasını okuyup veriyi döndüren API endpoint'i."""
    try:
        with open(RESULTS_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except (FileNotFoundError, json.JSONDecodeError):
        # Dosya yoksa veya boşsa, boş liste döndür
        return jsonify([])

@app.route('/guide')
def guide():
    return render_template('guide.html')