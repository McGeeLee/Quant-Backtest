import streamlit as st
import akshare as ak
import pandas as pd
import yfinance as yf
import time

def get_akshare_data(symbol, start_date, end_date):
    """
    调试 AKShare 数据源 (含 yfinance 自动兜底)
    symbol 格式: 600519
    """
    s = start_date.replace("-", "")
    e = end_date.replace("-", "")
    
    # --- 尝试路径 A: AKShare (东财接口) ---
    try:
        st.info("尝试从 AKShare (东财) 获取数据...")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=s, end_date=e, adjust="qfq")
        if not df.empty:
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as err:
        st.warning(f"⚠️ AKShare 连接受阻: {err}")
        st.write("正在切换至海外兜底数据源 (Yahoo Finance)...")
        time.sleep(1) # 稍微等待避免请求过快

    # --- 尝试路径 B: yfinance (海外服务器极其稳定) ---
    try:
        # yfinance 格式处理: 600519 -> 600519.SS
        yf_symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
        data = yf.download(yf_symbol, start=start_date, end=end_date)
        
        if not data.empty:
            df = data.reset_index()
            # yfinance 可能返回 MultiIndex，强制扁平化处理
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            st.success("✅ 通过 Yahoo Finance 成功获取数据！")
            return df
    except Exception as yf_err:
        st.error(f"❌ 所有 A 股数据源均失效: {yf_err}")
    
    return pd.DataFrame()