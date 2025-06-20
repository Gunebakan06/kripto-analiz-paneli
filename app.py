# =================================================================
# === Web Arayüzü Sunucusu (app.py) ===
# Sadece web sayfasını sunar, ayarları kaydeder.
# =================================================================
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from database import init_db, save_settings, load_settings, get_analysis_results, get_market_status

# Varsayılan Ayarlar
DEFAULT_SETTINGS = {
    'total_capital': 100000.0, 'risk_percent': 1.0, 'max_pos_percent': 10.0,
    'weight_ma': 30, 'weight_rsi': 20, 'weight_volume': 15,
    'weight_macd': 15, 'weight_bb': 10, 'weight_adx': 10
}

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    """Ana dashboard sayfasını yönetir."""
    if request.method == 'POST':
        # Formdan gelen ayarları al ve veritabanına kaydet
        current_settings = load_settings(DEFAULT_SETTINGS)
        for key in DEFAULT_SETTINGS.keys():
            form_value = request.form.get(key)
            if form_value and form_value.strip():
                try:
                    current_settings[key] = float(form_value) if '.' in form_value else int(form_value)
                except ValueError:
                    print(f"Uyarı: Formdaki '{key}' değeri geçersiz.")
        save_settings(current_settings)
        return redirect(url_for('dashboard'))

    # Veritabanından en son ayarları, analiz sonuçlarını ve piyasa durumunu çek
    settings = load_settings(DEFAULT_SETTINGS)
    analysis_results = get_analysis_results()
    market_status = get_market_status()
    
    sorted_data_list = []
    if not analysis_results.empty:
        sorted_data_list = analysis_results.sort_values(by='score', ascending=False).to_dict('records')

    return render_template('dashboard.html',
                           coins=sorted_data_list,
                           settings=settings,
                           market_status=market_status)

@app.route('/guide')
def guide():
    return render_template('guide.html')

if __name__ == '__main__':
    # Bu dosya doğrudan çalıştırıldığında web sunucusunu başlat
    app.run(host='0.0.0.0', port=5000, debug=False)
