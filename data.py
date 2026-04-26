import streamlit as st
import pandas as pd
import akshare as ak
import tushare as ts
from tiingo import TiingoClient
from binance.client import Client as BinanceClient
from datetime import datetime

class DataManager:
    def __init__(self):
        # 1. 初始化 Tiingo
        tiingo_config = {'api_key': st.secrets["TIINGO_KEY"], 'session': True}
        self.tiingo_client = TiingoClient(tiingo_config)
        
        # 2. 初始化 Tushare
        ts.set_token(st.secrets["TUSHARE_TOKEN"])
        self.ts_pro = ts.pro_api()

        # 3. 初始化 Binance (获取公开K线通常不需要key，这里备用)
        self.binance_client = BinanceClient()

    @st.cache_data(ttl=3600)
    def get_us_stock(self, symbol, start, end):
        """Tiingo: 获取美股/ETF"""
        df = self.tiingo_client.get_dataframe(symbol, startDate=start, endDate=end)
        # 统一列名
        df.index.name = 'Date'
        return df.reset_index()

    @st.cache_data(ttl=3600)
    def get_a_stock_ak(self, symbol, start="20230101", end="20231231"):
        """AKShare: 免费获取A股历史数据 (推荐用于回测)"""
        # symbol 格式如 "600519"
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="hfq")
        df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Date'] = pd.to_datetime(df['Date'])
        return df

    @st.cache_data(ttl=3600)
    def get_crypto_binance(self, symbol="BTCUSDT", interval="1d", limit=500):
        """Binance: 获取加密货币 K 线"""
        klines = self.binance_client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'Close_time', 'Quote_av', 'Trades', 'Tb_base_av', 'Tb_quote_av', 'Ignore'
        ])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[cols] = df[cols].apply(pd.to_numeric)
        return df[['Date'] + cols]

    @st.cache_data(ttl=3600)
    def get_macro_data(self, indicator="中国宏观杠杆率"):
        """AKShare: 获取宏观经济数据"""
        # AKShare 强在宏观、利率、情绪数据
        return ak.macro_cnbs()

# 实例化
data_manager = DataManager()