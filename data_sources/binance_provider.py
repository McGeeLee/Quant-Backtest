import streamlit as st
import pandas as pd
import requests
import yfinance as yf

def get_binance_data(symbol="BTCUSDT", interval="1d", limit=500):
    st.info(f"正在尝试多源调取加密货币数据: {symbol}...")
    
    # 1. 尝试修正后的 Binance.us 接口 (针对美区服务器)
    try:
        # Binance.us 的标准路径是 /api/v3/
        us_url = f"https://api.binance.us/api/v3/klines"
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        res = requests.get(us_url, params=params, timeout=5)
        if res.status_code == 200:
            st.success("✅ 通过 Binance.us 接口成功获取数据！")
            klines = res.json()
            df = pd.DataFrame(klines).iloc[:, :6]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            return df
    except:
        pass

    # 2. 尝试 yfinance 兜底 (全球最稳，无需 Key)
    try:
        st.write("正在尝试 Yahoo Finance 兜底获取 (BTC-USD 格式)...")
        # 转换格式: BTCUSDT -> BTC-USD
        yf_symbol = symbol.replace("USDT", "-USD")
        # 映射 interval
        yf_interval = "1d" if interval == "1d" else "1h"
        
        data = yf.download(yf_symbol, period="max" if limit > 100 else "1mo", interval=yf_interval)
        if not data.empty:
            df = data.reset_index()
            # 处理可能的 MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            st.success("✅ 通过 Yahoo Finance 成功获取加密货币数据！")
            return df
    except Exception as e:
        st.error(f"❌ 所有加密货币数据源均失效: {e}")
        
    return pd.DataFrame()