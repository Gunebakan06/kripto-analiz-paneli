# task.py - Veri İşçisi Scripti
import pandas as pd
import time
import json
import os

from data_fetcher import get_all_try_symbols, fetch_ohlcv_data
from analyzer import calculate_indicators

# Ayarların ve sonuçların kaydedileceği yol.
# Render'da bu /data/shared olacak.
DATA_PATH = os.environ.get('DATA_PATH', '.') 
SETTINGS_FILE = os.path.join(DATA_PATH, 'settings.db')
RESULTS_FILE = os.path.join(DATA_PATH, 'results.json')

# Yerel veritabanı kütüphanesini burada import ediyoruz
from database import load_settings, init_db

def run_full_analysis():
    """Tüm pariteler için analiz yapan merkezi fonksiyon."""
    print("Tam analiz döngüsü başlıyor...")

    # Bu satır init_db() fonksiyonunun settings.db'yi doğru yerde oluşturmasını sağlar
    # database.py dosyasındaki DB_FILE değişkenini güncelledik.
    import database
    database.DB_FILE = SETTINGS_FILE

    settings = load_settings({
        'total_capital': 100000.0, 'risk_percent': 1.0, 'max_pos_percent': 10.0,
        'weight_ma': 30, 'weight_rsi': 20, 'weight_volume': 15,
        'weight_macd': 15, 'weight_bb': 10, 'weight_adx': 10
    })

    symbols = get_all_try_symbols()
    all_results = []

    for i, symbol_with_slash in enumerate(symbols):
        print(f"Analiz ediliyor: {symbol_with_slash} ({i+1}/{len(symbols)})")
        time.sleep(0.1)

        coin_df = fetch_ohlcv_data(symbol_with_slash, timeframe='5m', limit=100)

        if coin_df is not None and not coin_df.empty:
            result = calculate_indicators(coin_df, settings)
            if result:
                all_results.append(result)

    if all_results:
        df = pd.DataFrame(all_results)
        df.to_json(RESULTS_FILE, orient='records', indent=4)
        print(f"Analiz tamamlandı. {len(df)} adet uygun coin sonucu {RESULTS_FILE} dosyasına kaydedildi.")
    else:
        print("Analiz tamamlandı. Uygun coin bulunamadı.")

if __name__ == '__main__':
    run_full_analysis()