import streamlit as st
from data_sources.tushare_provider import get_tushare_data
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.title("🛠️ 数据源专项调试: Tushare")

# 侧边栏配置
st.sidebar.header("Tushare 配置")
ticker = st.sidebar.text_input("输入代码 (需带后缀)", value="600519.SH")
days = st.sidebar.slider("获取天数", 30, 365, 100)

start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
end = datetime.now().strftime('%Y-%m-%d')

if st.sidebar.button("开始调试"):
    df = get_tushare_data(ticker, start, end)
    
    if not df.empty:
        st.success(f"成功连接 Tushare！获取到 {len(df)} 行数据")
        st.dataframe(df.tail())
        
        # 画个简单的图确认数据质量
        fig = go.Figure(data=[go.Scatter(x=df['Date'], y=df['Close'], name="收盘价")])
        st.plotly_chart(fig)
    else:
        st.warning("未能获取数据，请检查：1.Token是否正确 2.权限(积分)是否足够 3.代码后缀是否正确")