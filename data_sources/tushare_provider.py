import streamlit as st
import tushare as ts
import pandas as pd

def get_tushare_data(symbol, start_date, end_date):
    """
    调试 Tushare 数据源
    symbol 格式: 000001.SZ 或 600519.SH
    """
    token = st.secrets.get("TUSHARE_TOKEN")
    if not token:
        st.error("❌ 缺少 TUSHARE_TOKEN，请在 Secrets 中配置")
        return pd.DataFrame()

    try:
        ts.set_token(token)
        pro = ts.pro_api()
        # Tushare 格式需要 YYYYMMDD
        s = start_date.replace("-", "")
        e = end_date.replace("-", "")
        
        df = pro.daily(ts_code=symbol, start_date=s, end_date=e)
        
        if not df.empty:
            # Tushare 返回的是倒序，且列名是大写，需要转换
            df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol']]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Tushare 调试报错: {e}")
        return pd.DataFrame()