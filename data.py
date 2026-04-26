import streamlit as st
import pandas as pd
import tushare as ts
import yfinance as yf
from tiingo import TiingoClient

# --- 核心逻辑 ---

@st.cache_data(ttl=3600)
def _fetch_tushare_logic(symbol, start, end):
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
def _fetch_yahoo_logic(symbol, start, end, interval="1d"):
    try:
        data = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
        if not data.empty:
            df = data.reset_index()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            # 统一列名映射，防止不同源的大小写差异导致 KeyError
            df.columns = [c.capitalize() for c in df.columns]
            return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    except Exception as e:
        st.error(f"Yahoo 接口报错: {e}")
    return pd.DataFrame()

class DataManager:
    def __init__(self):
        self.tiingo_key = st.secrets.get("TIINGO_KEY")
        self.tiingo_client = TiingoClient({'api_key': self.tiingo_key}) if self.tiingo_key else None

    def get_data(self, source_type, ticker, start, end, **kwargs):
        if source_type == "Tushare":
            return _fetch_tushare_logic(ticker, start, end)
        elif source_type == "Tiingo" and self.tiingo_client:
            try:
                df = self.tiingo_client.get_dataframe(ticker, startDate=start, endDate=end)
                df = df.reset_index()
                df.columns = [c.capitalize() for c in df.columns] # 强制转换首字母大写
                return df
            except:
                return pd.DataFrame()
        elif source_type == "Yahoo":
            return _fetch_yahoo_logic(ticker, start, end, interval=kwargs.get('interval', '1d'))
        return pd.DataFrame()

data_manager = DataManager()