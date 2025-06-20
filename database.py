import sqlite3
import pandas as pd
import json
import os

# Render'da ortam değişkeni olarak ayarlanacak, yerelde ise 'data' klasörü oluşturulacak.
DATA_DIR = os.environ.get('RENDER_DATA_DIR', 'data')
DB_FILE = os.path.join(DATA_DIR, 'settings.db')
RESULTS_FILE = os.path.join(DATA_DIR, 'analysis_results.json')
STATUS_FILE = os.path.join(DATA_DIR, 'market_status.json')

def init_db():
    """Gerekli klasörü ve ayarlar veritabanını oluşturur."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    conn = sqlite3.connect(DB_FILE)
    conn.execute('PRAGMA journal_mode=WAL;') # Eş zamanlı erişim için
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_settings(settings_dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                   ('analysis_settings', json.dumps(settings_dict)))
    conn.commit()
    conn.close()

def load_settings(default_settings):
    init_db()
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", ('analysis_settings',))
        row = cursor.fetchone()
        conn.close()
        if row: return json.loads(row[0])
    except:
        pass
    
    save_settings(default_settings)
    return default_settings

def save_analysis_results(df_analysis):
    """Analiz sonuçlarını bir JSON dosyasına kaydeder."""
    df_analysis.to_json(RESULTS_FILE, orient='records', indent=4)

def get_analysis_results():
    """Analiz sonuçlarını JSON dosyasından okur."""
    try:
        return pd.read_json(RESULTS_FILE)
    except (FileNotFoundError, ValueError):
        return pd.DataFrame()

def update_market_status(status_text):
    color = 'success' if 'YÜKSELİŞTE' in status_text else 'danger'
    status = {'text': status_text, 'color': color}
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f)

def get_market_status():
    """Piyasa durumunu JSON dosyasından okur."""
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'text': 'Henüz Belirlenmedi', 'color': 'secondary'}

# Eski veri çekme ve temizleme fonksiyonları artık kullanılmadığı için kaldırıldı.
