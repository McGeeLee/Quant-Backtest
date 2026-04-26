import streamlit as st
import pandas as pd
import numpy as np
import requests
import akshare as ak
import tushare as ts
from tiingo import TiingoClient
from binance.client import Client as BinanceClient
from datetime import datetime

class DataManager:
    def __init__(self):
        """初始化各个数据源的配置，采用非阻塞方式防止单个源失效导致整站崩溃"""
        
        # --- 1. Tiingo 配置 ---
        self.tiingo_key = st.secrets.get("TIINGO_KEY")
        self.tiingo_client = None
        if self.tiingo_key:
            try:
                self.tiingo_client = TiingoClient({'api_key': self.tiingo_key, 'session': True})
            except Exception:
                st.sidebar.error("Tiingo 客户端初始化失败")

        # --- 2. Tushare 配置 ---
        self.ts_token = st.secrets.get("TUSHARE_TOKEN")
        self.ts_pro = None
        if self.ts_token:
            try:
                ts.set_token(self.ts_token)
                self.ts_pro = ts.pro_api()
            except Exception:
                st.sidebar.error("Tushare 令牌无效")

        # --- 3. Binance 配置 ---
        self.binance_client = None
        try:
            # 尝试连接，不带 API Key 仅用于获取公开 K 线数据
            # 如果在美区服务器报错，尝试添加 tld='us'
            self.binance_client = BinanceClient(tld='com') 
        except Exception:
            # 即使报错也不在此中断，后面会有 requests 兜底
            pass

    @st.cache_data(ttl=3600)
    def get_us_stock(self, _self, symbol: str, start: str, end: str):
        """获取美股/ETF数据 (来自 Tiingo)"""
        if not self.tiingo_client:
            st.error("未配置 TIINGO_KEY")
            return pd.DataFrame()
        try:
            df = self.tiingo_client.get_dataframe(symbol, startDate=start, endDate=end)
            df.index.name = 'Date'
            return df.reset_index()
        except Exception as e:
            st.error(f"Tiingo 抓取失败: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)
    def get_a_stock(self, _self, symbol: str, start: str, end: str):
        """获取A股数据 (来自 AKShare, 免费且无需 Key)"""
        try:
            # AKShare 格式 YYYYMMDD
            s = start.replace("-", "")
            e = end.replace("-", "")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=s, end_date=e, adjust="qfq")
            if df.empty: return df
            
            # 统一列名
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            st.error(f"AKShare 抓取失败: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)
    def get_crypto(self, _self, symbol: str, interval: str = "1d", limit: int = 500):
        """获取加密货币数据 (Binance 官方库 + Requests 兜底)"""
        klines = None
        
        # 优先尝试官方 SDK
        if self.binance_client:
            try:
                klines = self.binance_client.get_klines(symbol=symbol, interval=interval, limit=limit)
            except:
                klines = None
        
        # SDK 失败则使用原生 Requests (绕过部分地理限制)
        if klines is None:
            try:
                url = f"https://api.binance.com/api/3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
                res = requests.get(url, timeout=10)
                klines = res.json()
            except Exception as e:
                st.error(f"Binance 所有接口连接失败: {e}")
                return pd.DataFrame()

        try:
            df = pd.DataFrame(klines, columns=[
                'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
                'Close_time', 'Quote_av', 'Trades', 'Tb_base_av', 'Tb_quote_av', 'Ignore'
            ])
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            st.error(f"数据解析失败: {e}")
            return pd.DataFrame()

# 实例化
data_manager = DataManager()