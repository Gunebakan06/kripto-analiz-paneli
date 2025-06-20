# =================================================================
# === Veritabanı Yönetimi (database.py) ===
# =================================================================
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

DB_FILE = "crypto_analysis.db"

def init_db():
    """Veritabanını ve gerekli tabloları oluşturur."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Ham veri tablosu (zaman ve pariteye göre benzersiz kayıtlar)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            volume REAL NOT NULL,
            UNIQUE(timestamp, symbol)
        )
    ''')
    # Kullanıcı ayarları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_data_to_db(df):
    """Gelen anlık veriyi veritabanına kaydeder."""
    try:
        conn = sqlite3.connect(DB_FILE)
        df.dropna(subset=['price', 'volume'], inplace=True)
        df = df[df['price'] > 0]
        if df.empty:
            conn.close()
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['timestamp'] = timestamp
        df = df[['timestamp', 'symbol', 'price', 'volume']]
        
        # UNIQUE kısıtlaması ihlal edilirse hata vermeden devam etmesi için
        df.to_sql('historical_data', conn, if_exists='append', index=False)
        conn.close()
    except sqlite3.IntegrityError:
        print("Uyarı: Veritabanına eklenmeye çalışılan bazı veriler zaten mevcuttu. Atlandı.")
    except Exception as e:
        print(f"Veritabanına kaydetme hatası: {e}")


def get_historical_data_as_df():
    """Tüm geçmiş verileri DataFrame olarak döndürür."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM historical_data", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

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
    init_db() # Başlamadan önce tablonun var olduğundan emin ol
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", ('analysis_settings',))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    else:
        return default_settings

def cleanup_old_data():
    """2 günden eski verileri siler."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    time_limit = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("DELETE FROM historical_data WHERE timestamp < ?", (time_limit,))
    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted_rows > 0:
        print(f"{deleted_rows} adet eski kayıt (2 günden eski) silindi.")
