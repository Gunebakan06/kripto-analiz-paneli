# =================================================================
# === Kullanıcı Dostu Kripto Analiz Uygulaması - app.py (Nihai) ===
# =================================================================
from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import logging
import time

# Loglamayı sadece temel hataları gösterecek şekilde ayarla
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.ERROR)

from data_fetcher import get_all_try_symbols, fetch_ohlcv_data
from database import init_db, save_settings, load_settings
from analyzer import calculate_indicators

# Varsayılan Ayarlar (eğer veritabanında hiç ayar yoksa kullanılır)
DEFAULT_SETTINGS = {
    'total_capital': 100000.0, 'risk_percent': 1.0, 'max_pos_percent': 10.0,
    'weight_ma': 30, 'weight_rsi': 20, 'weight_volume': 15,
    'weight_macd': 15, 'weight_bb': 10, 'weight_adx': 10
}

app = Flask(__name__)

analysis_data = pd.DataFrame()
market_status = {'text': 'Yükleniyor...', 'color': 'secondary'}

def run_full_analysis():
    """Tüm pariteler için analiz yapan merkezi fonksiyon."""
    global analysis_data, market_status
    print("Tam analiz döngüsü başlıyor...")
    
    settings = load_settings(DEFAULT_SETTINGS)
    symbols = get_all_try_symbols()
    all_results = []

    for i, symbol_with_slash in enumerate(symbols):
        # print(f"Analiz ediliyor: {symbol_with_slash} ({i+1}/{len(symbols)})")
        time.sleep(0.1)
        
        coin_df = fetch_ohlcv_data(symbol_with_slash, timeframe='5m', limit=100)
        
        if coin_df is not None and not coin_df.empty:
            result = calculate_indicators(coin_df, settings)
            if result:
                all_results.append(result)
    
    if all_results:
        analysis_data = pd.DataFrame(all_results)
        print(f"Analiz tamamlandı. {len(analysis_data)} adet uygun coin bulundu.")
    else:
        # Eğer hiç sonuç yoksa, en azından boş bir DataFrame olduğundan emin ol
        analysis_data = pd.DataFrame()
        print("Analiz tamamlandı. Uygun coin bulunamadı.")
    
    # Piyasa durumunu belirle
    btc_df = fetch_ohlcv_data('BTC/TRY', timeframe='5m', limit=50)
    if btc_df is not None and not btc_df.empty:
        btc_price = btc_df['close'].iloc[-1]
        btc_ma50 = btc_df['close'].mean()
        if btc_price > btc_ma50:
            market_status = {'text': 'PİYASA YÜKSELİŞTE - ALIMA UYGUN', 'color': 'success'}
        else:
            market_status = {'text': 'PİYASA DÜŞÜŞTE - RİSKLİ', 'color': 'danger'}

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    """Ana dashboard sayfasını yönetir. Ayarları alır, günceller ve sonuçları gösterir."""
    if request.method == 'POST':
        current_settings = load_settings(DEFAULT_SETTINGS)
        form = request.form
        
        # Formdan gelen değerleri al ve ayarları güncelle
        for key in DEFAULT_SETTINGS.keys():
            try:
                # Değeri doğru tipe çevir (float veya int)
                if '.' in form.get(key, ''):
                    current_settings[key] = float(form.get(key))
                else:
                    current_settings[key] = int(form.get(key))
            except (ValueError, TypeError):
                print(f"Formdaki '{key}' değeri geçersiz veya boş, önceki değer korunuyor.")
        
        save_settings(current_settings)
        run_full_analysis() # Ayarlar güncellenince analizi hemen yeniden çalıştır
        return redirect(url_for('dashboard'))
        
    settings = load_settings(DEFAULT_SETTINGS)
    sorted_data_list = []
    if not analysis_data.empty and 'score' in analysis_data.columns:
        sorted_data_list = analysis_data.sort_values(by='score', ascending=False).to_dict('records')

    return render_template('dashboard.html',
                           coins=sorted_data_list,
                           settings=settings,
                           market_status=market_status)

@app.route('/guide')
def guide():
    return render_template('guide.html')

if __name__ == '__main__':
    init_db()
    run_full_analysis()

    scheduler = BackgroundScheduler(daemon=True)
    # Analiz ve veri çekme işlemi zaman aldığı için periyodu 15 dakikaya çıkaralım
    scheduler.add_job(func=run_full_analysis, trigger="interval", minutes=15)
    scheduler.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
