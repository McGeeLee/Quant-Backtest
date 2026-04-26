import streamlit as st
import pandas as pd
import requests
import akshare as ak
import tushare as ts
from tiingo import TiingoClient
from binance.client import Client as BinanceClient

# --- 将具体的获取逻辑放在类外面，并使用下划线开头的参数名避免 Hash ---

@st.cache_data(ttl=3600)
def _fetch_us_stock_logic(_tiingo_client, symbol, start, end):
    df = _tiingo_client.get_dataframe(symbol, startDate=start, endDate=end)
    return df.reset_index()

@st.cache_data(ttl=3600)
def _fetch_a_stock_logic(symbol, start, end):
    s = start.replace("-", "")
    e = end.replace("-", "")
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=s, end_date=e, adjust="qfq")
    if not df.empty:
        df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Date'] = pd.to_datetime(df['Date'])
    return df

@st.cache_data(ttl=3600)
def _fetch_crypto_logic(_binance_client, symbol, interval, limit):
    klines = None
    if _binance_client:
        try:
            klines = _binance_client.get_klines(symbol=symbol, interval=interval, limit=limit)
        except:
            klines = None
    
    if klines is None:
        url = f"https://api.binance.com/api/3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=10)
        klines = res.json()

    df = pd.DataFrame(klines, columns=[
        'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
        'Close_time', 'Quote_av', 'Trades', 'Tb_base_av', 'Tb_quote_av', 'Ignore'
    ])
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

# --- DataManager 类现在只负责管理 Key 和分发调用 ---

class DataManager:
    def __init__(self):
        self.tiingo_key = st.secrets.get("TIINGO_KEY")
        self.tiingo_client = None
        if self.tiingo_key:
            self.tiingo_client = TiingoClient({'api_key': self.tiingo_key, 'session': True})

        self.binance_client = None
        try:
            self.binance_client = BinanceClient(tld='com')
        except:
            pass

    def get_us_stock(self, symbol, start, end):
        if not self.tiingo_client:
            st.error("未配置 TIINGO_KEY")
            return pd.DataFrame()
        return _fetch_us_stock_logic(self.tiingo_client, symbol, start, end)

    def get_a_stock(self, symbol, start, end):
        return _fetch_a_stock_logic(symbol, start, end)

    def get_crypto(self, symbol, interval="1d", limit=500):
        return _fetch_crypto_logic(self.binance_client, symbol, interval, limit)

data_manager = DataManager()