import streamlit as st
from data_sources.akshare_provider import get_akshare_data # 修改导入
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.title("🛠️ 数据源专项调试: A股 (AKShare/YF)")

ticker = st.sidebar.text_input("输入代码 (不带后缀)", value="600519")
days = st.sidebar.slider("获取天数", 30, 365, 100)

start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
end = datetime.now().strftime('%Y-%m-%d')

if st.sidebar.button("开始调试 A股"):
    df = get_akshare_data(ticker, start, end)
    
    if not df.empty:
        st.success(f"获取成功！共 {len(df)} 行记录")
        # 画 K 线图确认格式
        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
        )])
        st.plotly_chart(fig)
        st.dataframe(df.tail())