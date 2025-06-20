# =================================================================
# === Kullanıcı Dostu Kripto Analiz Uygulaması - app.py ===
# =================================================================
from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import logging

# Loglamayı sadece temel hataları gösterecek şekilde ayarla
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.ERROR)

from data_fetcher import fetch_all_try_data
from database import init_db, save_data_to_db, cleanup_old_data, get_historical_data_as_df, save_settings, load_settings
from analyzer import calculate_indicators

# Varsayılan Ayarlar
DEFAULT_SETTINGS = {
    'total_capital': 100000.0, 'risk_percent': 1.0, 'max_pos_percent': 10.0,
    'weight_ma': 30, 'weight_rsi': 20, 'weight_volume': 15,
    'weight_macd': 15, 'weight_bb': 10, 'weight_adx': 10
}

app = Flask(__name__)

analysis_data = pd.DataFrame()
market_status = {'text': 'Yükleniyor...', 'color': 'secondary'}

# --- Ana analiz fonksiyonu ---
def run_analysis():
    global analysis_data, market_status
    print("Analiz çalıştırılıyor...")
    settings = load_settings(DEFAULT_SETTINGS)
    df_hist = get_historical_data_as_df()

    if not df_hist.empty:
        analysis_data = calculate_indicators(df_hist, settings)
        print(f"Analiz sonucunda {len(analysis_data)} adet uygun coin bulundu.")

        btc_data = df_hist[df_hist['symbol'] == 'BTCTRY']
        if len(btc_data) > 50:
            btc_price = btc_data['price'].iloc[-1]
            btc_ma50 = btc_data['price'].rolling(window=50).mean().iloc[-1]
            if btc_price > btc_ma50:
                market_status = {'text': 'PİYASA YÜKSELİŞTE - ALIMA UYGUN', 'color': 'success'}
            else:
                market_status = {'text': 'PİYASA DÜŞÜŞTE - RİSKLİ', 'color': 'danger'}
        else:
            market_status = {'text': 'BTC Verisi Bekleniyor...', 'color': 'warning'}
    print("Analiz tamamlandı.")

# --- Arka plan zamanlayıcı görevi ---
def job_background_task():
    print("="*50)
    print("Arka plan görevi başlıyor...")
    df_current = fetch_all_try_data()
    if not df_current.empty:
        save_data_to_db(df_current)
    run_analysis()
    cleanup_old_data()
    print("Arka plan görevi tamamlandı.")
    print("="*50)

# --- Ana Sayfa ---
@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        current_settings = load_settings(DEFAULT_SETTINGS)
        form = request.form
        
        # --- GÜVENLİ FORM İŞLEME ---
        for key in DEFAULT_SETTINGS:
            form_value = form.get(key)
            if form_value and form_value.strip(): # Değer boş değilse
                try:
                    # Değeri doğru tipe çevir (float veya int)
                    current_settings[key] = float(form_value) if '.' in form_value else int(form_value)
                except ValueError:
                    print(f"Uyarı: Formdaki '{key}' değeri geçersiz, önceki değer korunuyor.")
        
        save_settings(current_settings)
        run_analysis()
        return redirect(url_for('dashboard'))

    settings = load_settings(DEFAULT_SETTINGS)
    sorted_data_list = []
    if not analysis_data.empty and 'score' in analysis_data.columns:
        sorted_data_list = analysis_data.sort_values(by='score', ascending=False).to_dict('records')

    return render_template('dashboard.html',
                           coins=sorted_data_list,
                           settings=settings,
                           market_status=market_status)

# --- Kullanım Kılavuzu Sayfası ---
@app.route('/guide')
def guide():
    return render_template('guide.html')

# --- Başlatıcı ---
if __name__ == '__main__':
    init_db()
    job_background_task()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=job_background_task, trigger="interval", minutes=5)
    scheduler.start()
    
    # Debug modunu kapatmak, zamanlayıcının iki kez çalışmasını engeller
    # ve sistemi daha stabil hale getirir.
    app.run(host='0.0.0.0', port=5000, debug=False)
