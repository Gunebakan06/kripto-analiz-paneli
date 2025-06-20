# =================================================================
# === Arka Plan İşçisi (worker.py) ===
# Render'da sürekli çalışır ve periyodik olarak analiz yapar.
# =================================================================
from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd
import time
import logging

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.ERROR)

from data_fetcher import get_all_try_symbols, fetch_ohlcv_data
from database import init_db, save_data_to_db, save_settings, load_settings, save_analysis_results, update_market_status
from analyzer import calculate_indicators

DEFAULT_SETTINGS = {
    'total_capital': 100000.0, 'risk_percent': 1.0, 'max_pos_percent': 10.0,
    'weight_ma': 30, 'weight_rsi': 20, 'weight_volume': 15,
    'weight_macd': 15, 'weight_bb': 10, 'weight_adx': 10
}

def run_full_analysis():
    """Tüm pariteler için analiz yapan merkezi fonksiyon."""
    print("="*50)
    print("Tam analiz döngüsü başlıyor...")
    
    settings = load_settings(DEFAULT_SETTINGS)
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
        analysis_df = pd.DataFrame(all_results)
        save_analysis_results(analysis_df)
        print(f"Analiz tamamlandı. {len(analysis_df)} adet sonuç veritabanına kaydedildi.")
    else:
        print("Analiz tamamlandı. Uygun coin bulunamadı.")
    
    # Piyasa durumunu belirle ve veritabanına kaydet
    btc_df = fetch_ohlcv_data('BTC/TRY', timeframe='5m', limit=50)
    if btc_df is not None and not btc_df.empty:
        btc_price = btc_df['close'].iloc[-1]
        btc_ma50 = btc_df['close'].mean()
        status_text = 'PİYASA YÜKSELİŞTE - ALIMA UYGUN' if btc_price > btc_ma50 else 'PİYASA DÜŞÜŞTE - RİSKLİ'
        update_market_status(status_text)
    
    print("Analiz döngüsü tamamlandı.")
    print("="*50)

if __name__ == '__main__':
    init_db()
    
    # Hemen bir kez çalıştır
    run_full_analysis()
    
    # Her 15 dakikada bir çalışacak zamanlayıcıyı kur
    scheduler = BlockingScheduler()
    scheduler.add_job(run_full_analysis, 'interval', minutes=15)
    
    print("Arka plan işçisi başlatıldı. Her 15 dakikada bir analiz yapılacak.")
    scheduler.start()
