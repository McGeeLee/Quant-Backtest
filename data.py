import streamlit as st
import pandas as pd
import requests
import akshare as ak
import tushare as ts
import yfinance as yf
import time
from tiingo import TiingoClient

# --- 核心获取逻辑 (支持缓存与自动保底) ---

@st.cache_data(ttl=3600)
def _fetch_tushare_logic(symbol, start, end):
    """Tushare 获取逻辑"""
    token = st.secrets.get("TUSHARE_TOKEN")
    if not token:
        st.error("❌ 缺少 TUSHARE_TOKEN")
        return pd.DataFrame()
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        s, e = start.replace("-", ""), end.replace("-", "")
        df = pro.daily(ts_code=symbol, start_date=s, end_date=e)
        if not df.empty:
            df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol']]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])
            return df.sort_values('Date')
    except Exception as e:
        st.error(f"Tushare 报错: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def _fetch_a_stock_logic(symbol, start, end):
    """AKShare 获取逻辑，含 Yahoo 自动保底"""
    try:
        s, e = start.replace("-", ""), end.replace("-", "")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=s, end_date=e, adjust="qfq")
        if not df.empty:
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as err:
        st.warning(f"⚠️ AKShare 受阻，尝试 Yahoo Finance 兜底...")
        yf_symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
        return _fetch_yahoo_logic(yf_symbol, start, end)
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def _fetch_crypto_logic(symbol, interval, limit):
    """Binance 获取逻辑，含 451 状态码处理与 Yahoo 保底"""
    # 尝试 Binance.us (适合美区服务器)
    try:
        url = f"https://api.binance.us/api/v3/klines"
        res = requests.get(url, params={"symbol": symbol.upper(), "interval": interval, "limit": limit}, timeout=5)
        if res.status_code == 200:
            df = pd.DataFrame(res.json()).iloc[:, :6]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            return df
    except:
        pass
    
    st.warning("⚠️ Binance 接口受限，切换至 Yahoo Finance...")
    yf_symbol = symbol.replace("USDT", "-USD")
    return _fetch_yahoo_logic(yf_symbol, None, None, interval=interval, period="1mo")

@st.cache_data(ttl=3600)
def _fetch_yahoo_logic(symbol, start, end, interval="1d", period=None):
    """Yahoo Finance 基础获取逻辑"""
    try:
        data = yf.download(symbol, start=start, end=end, period=period, interval=interval, progress=False)
        if not data.empty:
            df = data.reset_index()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            return df
    except Exception as e:
        st.error(f"Yahoo 接口报错: {e}")
    return pd.DataFrame()

# --- DataManager 管理类 ---

class DataManager:
    def __init__(self):
        self.tiingo_key = st.secrets.get("TIINGO_KEY")
        self.tiingo_client = TiingoClient({'api_key': self.tiingo_key}) if self.tiingo_key else None

    def get_data(self, source_type, ticker, start, end, **kwargs):
        """统一数据分发入口"""
        if source_type == "Tushare":
            return _fetch_tushare_logic(ticker, start, end)
        elif source_type == "AKShare":
            return _fetch_a_stock_logic(ticker, start, end)
        elif source_type == "Binance":
            return _fetch_crypto_logic(ticker, kwargs.get('interval', '1d'), kwargs.get('limit', 500))
        elif source_type == "Yahoo":
            return _fetch_yahoo_logic(ticker, start, end, interval=kwargs.get('interval', '1d'))
        elif source_type == "Tiingo" and self.tiingo_client:
            df = self.tiingo_client.get_dataframe(ticker, startDate=start, endDate=end)
            return df.reset_index()
        return pd.DataFrame()

data_manager = DataManager()