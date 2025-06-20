# =================================================================
# === Gelişmiş Analiz Motoru (analyzer.py) - OHLCV Uyumlu ===
# =================================================================
import pandas as pd
import pandas_ta as ta

def calculate_indicators(coin_df, settings):
    """
    Tek bir coin'in OHLCV DataFrame'ini alıp tüm analizleri yapar.
    """
    try:
        # --- TÜM TEKNİK İNDİKATÖRLERİ HESAPLA ---
        coin_df.ta.ema(length=20, append=True)
        coin_df.ta.ema(length=50, append=True)
        coin_df.ta.rsi(length=14, append=True)
        coin_df.ta.stdev(length=14, append=True)
        coin_df.ta.macd(fast=12, slow=26, signal=9, append=True)
        coin_df.ta.bbands(length=20, std=2, append=True)
        coin_df.ta.adx(length=14, append=True)
        
        last_row = coin_df.iloc[-1]
        if last_row.isnull().any():
            return None # Herhangi bir indikatör hesaplanamadıysa bu coini atla

        anlik_fiyat = last_row['close']

        # --- AĞIRLIKLI PUANLAMA İÇİN ALT SKORLAR ---
        ma_score = 100 if last_row['EMA_20'] > last_row['EMA_50'] else 0
        rsi_score = 100 if 40 < last_row['RSI_14'] < 65 else (50 if 35 < last_row['RSI_14'] <= 40 or 65 <= last_row['RSI_14'] < 75 else 0)
        volume_change_1h = coin_df['volume'].pct_change(periods=12).iloc[-1]
        volume_score = 100 if pd.notna(volume_change_1h) and volume_change_1h > 0.10 else 0
        macd_score = 100 if last_row['MACD_12_26_9'] > last_row['MACDs_12_26_9'] else 0
        bb_score = 100 if last_row['BBM_20_2.0'] < anlik_fiyat < last_row['BBU_20_2.0'] else 0
        adx_score = 100 if last_row['ADX_14'] > 25 else 0

        # --- FİNAL PUAN ---
        total_score = (
            (ma_score * settings.get('weight_ma', 30)) +
            (rsi_score * settings.get('weight_rsi', 20)) +
            (volume_score * settings.get('weight_volume', 15)) +
            (macd_score * settings.get('weight_macd', 15)) +
            (bb_score * settings.get('weight_bb', 10)) +
            (adx_score * settings.get('weight_adx', 10))
        ) / 100.0

        # --- RİSK METRİKLERİ ---
        volatilite = last_row['STDEV_14']
        stop_loss = anlik_fiyat - (volatilite * 1.5)
        
        risk_amount = settings.get('total_capital', 100000) * (settings.get('risk_percent', 1.0) / 100.0)
        max_position = settings.get('total_capital', 100000) * (settings.get('max_pos_percent', 10.0) / 100.0)
        
        pozisyon_tl = 0
        if (anlik_fiyat > stop_loss):
            pozisyon_tl = (risk_amount / (anlik_fiyat - stop_loss)) * anlik_fiyat
            if pozisyon_tl > max_position:
                pozisyon_tl = max_position
        
        # Sonuçları tek bir satır olarak döndür
        return {
            'symbol': coin_df['symbol'].iloc[0], 'price': anlik_fiyat, 'ma20': last_row['EMA_20'],
            'ma50': last_row['EMA_50'], 'rsi': last_row['RSI_14'], 'volatility': volatilite,
            'score': total_score, 'stop_loss': stop_loss, 'position_tl': pozisyon_tl,
            'macd': last_row['MACD_12_26_9'], 'macd_signal': last_row['MACDs_12_26_9'],
            'bb_lower': last_row['BBL_20_2.0'], 'bb_upper': last_row['BBU_20_2.0'],
            'adx': last_row['ADX_14']
        }
    except Exception:
        return None
