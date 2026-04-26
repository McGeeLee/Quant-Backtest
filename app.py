import streamlit as st
from data_sources.binance_provider import get_binance_data
import plotly.graph_objects as go

st.title("🛠️ 数据源专项调试: Binance (Crypto)")

ticker = st.sidebar.text_input("输入交易对 (如 BTCUSDT)", value="BTCUSDT")
interval = st.sidebar.selectbox("时间粒度", ["1d", "4h", "1h"])

if st.sidebar.button("开始调试 Binance"):
    df = get_binance_data(ticker, interval)
    
    if not df.empty:
        st.success(f"获取成功！最新价格: {df['Close'].iloc[-1]}")
        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
        )])
        fig.update_layout(xaxis_rangeslider_visible=False)
        st.plotly_chart(fig)
        st.dataframe(df.tail())