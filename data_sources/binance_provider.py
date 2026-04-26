import streamlit as st
import pandas as pd
import requests

def get_binance_data(symbol="BTCUSDT", interval="1d", limit=500):
    """
    调试 Binance 数据源 (绕过 SDK 的地理围栏检查)
    """
    st.info(f"正在尝试连接 Binance REST API (查询: {symbol})...")
    
    # 备选接口地址 (如果 api.binance.com 被封，尝试 api1, api2 或 .us)
    endpoints = [
        f"https://api.binance.com/api/3/klines",
        f"https://api1.binance.com/api/3/klines",
        f"https://api.binance.us/api/3/klines" # 针对美国服务器的兜底
    ]
    
    for url in endpoints:
        try:
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": limit
            }
            res = requests.get(url, params=params, timeout=10)
            
            if res.status_code == 200:
                klines = res.json()
                df = pd.DataFrame(klines, columns=[
                    'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
                    'C_time', 'Q_av', 'Trades', 'Tb_base', 'Tb_quote', 'Ignore'
                ])
                df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col])
                
                st.success(f"✅ 成功从接口获取数据: {url}")
                return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            else:
                st.warning(f"⚠️ 接口 {url} 返回状态码: {res.status_code}")
        except Exception as e:
            st.warning(f"❌ 无法连接至 {url}: {e}")
            
    return pd.DataFrame()