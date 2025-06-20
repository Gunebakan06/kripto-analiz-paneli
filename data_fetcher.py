# =================================================================
# === OHLCV Veri Çekici (data_fetcher.py) ===
# =================================================================
import ccxt
import pandas as pd

exchange = ccxt.binance()

def get_all_try_symbols():
    """Borsada işlem gören tüm uygun TRY paritelerini çeker."""
    try:
        exchange.load_markets()
        all_symbols = exchange.symbols
        try_symbols = [s for s in all_symbols if s.endswith('/TRY')]
        # İstenmeyen token'ları filtrele
        try_symbols = [s for s in try_symbols if all(x not in s for x in ['UP/', 'DOWN/', 'BEAR/', 'BULL/'])]
        print(f"Borsada analize uygun {len(try_symbols)} adet TRY paritesi bulundu.")
        return try_symbols
    except Exception as e:
        print(f"Hata: Parite listesi çekilemedi. {e}")
        return []

def fetch_ohlcv_data(symbol, timeframe='5m', limit=100):
    """Belirtilen bir coin için geçmiş OHLCV verisini çeker."""
    try:
        if not exchange.has['fetchOHLCV']:
            return None
        
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # Zaman damgasını okunabilir formata çevir
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol.replace('/', '') # Sembolü ekle
        return df

    except Exception as e:
        # print(f"Uyarı: '{symbol}' için OHLCV verisi çekilemedi. Hata: {e}")
        return None
