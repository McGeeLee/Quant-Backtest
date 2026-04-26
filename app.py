import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import data_manager  
from datetime import datetime, timedelta

st.set_page_config(page_title="Gemini Quant - 精简版", page_icon="📈", layout="wide")

st.title("📊 量化平台数据源验证")
# st.caption("已移除不稳定源，保留 Tushare / Tiingo / Yahoo Finance")

# 侧边栏
st.sidebar.header("⚙️ 配置")
source = st.sidebar.selectbox("选择数据源", ["Yahoo Finance", "Tushare", "Tiingo"])

# 自动处理代码格式提示
if "Yahoo" in source:
    ticker = st.sidebar.text_input("代码 (如 AAPL 或 .SS.SZ.BJ)", value="BTC-USD")
    s_type = "Yahoo"
elif "Tushare" in source:
    ticker = st.sidebar.text_input("代码 (.SH.SZ.BJ)", value="600519.SH")
    s_type = "Tushare"
else:
    ticker = st.sidebar.text_input("代码 (AAPL 或 TSLA)", value="AAPL")
    s_type = "Tiingo"

start_date = st.sidebar.date_input("开始日期", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("结束日期", datetime.now())

if st.sidebar.button("🚀 获取数据"):
    with st.spinner('执行调取...'):
        sd, ed = start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        df = data_manager.get_data(s_type, ticker, sd, ed)

        if not df.empty and 'Close' in df.columns:
            st.success(f"✅ 成功获取 {ticker} 数据")
            
            # 指标卡
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            change = last['Close'] - prev['Close']
            
            m1, m2, m3 = st.columns(3)
            m1.metric("收盘价", f"{last['Close']:.2f}")
            m2.metric("涨跌幅", f"{change:.2f}", f"{(change/prev['Close'])*100:.2f}%")
            m3.metric("成交量", f"{last['Volume']:.0f}")

            # K线图
            fig = go.Figure(data=[go.Candlestick(
                x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#ef5350', decreasing_line_color='#26a69a'
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("❌ 未能获取数据。请检查代码格式是否正确，或 API Key 是否生效。")

st.sidebar.markdown("---")
st.sidebar.caption("Gemini Quant v2.1")