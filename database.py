# =================================================================
# === Veritabanı Yönetimi (database.py) - Sadece Ayarlar İçin ===
# =================================================================
import sqlite3
import json

DB_FILE = "settings.db" # Sadece ayarları sakladığı için ismi basitleştirelim

def init_db():
    """Sadece ayarlar tablosunu oluşturan veritabanı başlatma fonksiyonu."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_settings(settings_dict):
    """Kullanıcı ayarlarını veritabanına kaydeder."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                   ('analysis_settings', json.dumps(settings_dict)))
    conn.commit()
    conn.close()

def load_settings(default_settings):
    """Kullanıcı ayarlarını veritabanından yükler. Yoksa varsayılanı kullanır."""
    init_db() # Tablonun var olduğundan emin ol
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", ('analysis_settings',))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        else:
            # Veritabanında ayar yoksa, varsayılanı kaydet ve döndür
            save_settings(default_settings)
            return default_settings
    except:
        return default_settings
