# =================================================================
# === Dinamik Veri Çekici (data_fetcher.py) ===
# =================================================================
import ccxt
import pandas as pd

# Borsa bağlantısını kur
exchange = ccxt.binance()

def get_all_try_symbols():
    """
    Borsada işlem gören ve sonunda '/TRY' olan tüm pariteleri çeker.
    Kaldıraçlı ve istenmeyen token'ları filtreler.
    """
    try:
        exchange.load_markets()
        all_symbols = exchange.symbols
        try_symbols = [s for s in all_symbols if s.endswith('/TRY')]
        try_symbols = [s for s in try_symbols if 'UP/' not in s and 'DOWN/' not in s and 'BEAR/' not in s and 'BULL/' not in s]
        print(f"Borsada analize uygun {len(try_symbols)} adet TRY paritesi bulundu.")
        return try_symbols
    except Exception as e:
        print(f"Hata: Parite listesi çekilemedi. {e}")
        return []

def fetch_all_try_data():
    """
    Tüm TRY paritelerinin anlık fiyat ve hacim verilerini çeker.
    """
    symbols_to_fetch = get_all_try_symbols()
    
    if not symbols_to_fetch:
        print("Veri çekilecek parite bulunamadı.")
        return pd.DataFrame()

    try:
        tickers = exchange.fetch_tickers(symbols_to_fetch)
        data = []
        for symbol, ticker in tickers.items():
            if ticker and ticker.get('last') is not None and ticker.get('quoteVolume') is not None:
                data.append({
                    'symbol': symbol.replace('/', ''),
                    'price': ticker['last'],
                    'volume': ticker['quoteVolume']
                })
        
        return pd.DataFrame(data)

    except Exception as e:
        print(f"Hata: Toplu veri çekme işlemi başarısız oldu. {e}")
        return pd.DataFrame()
