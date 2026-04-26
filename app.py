import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import data_manager  
from datetime import datetime, timedelta

# 1. 页面基本配置
st.set_page_config(page_title="量化交易平台", layout="wide")

st.title("📊 量化平台数据源验证")

# 2. 侧边栏：配置参数
st.sidebar.header("数据查询配置")

source = st.sidebar.selectbox(
    "选择数据源",
    ["Tiingo (美股/外汇)", "AKShare (A股历史)", "Binance (加密货币)"]
)

# 动态调整输入框
if source == "Tiingo (美股/外汇)":
    ticker = st.sidebar.text_input("输入代码 (Ticker)", value="AAPL")
    start_date = st.sidebar.date_input("开始日期", datetime.now() - timedelta(days=365))
    end_date = st.sidebar.date_input("结束日期", datetime.now())
    
elif source == "AKShare (A股历史)":
    ticker = st.sidebar.text_input("输入代码 (如 600519)", value="600519")
    start_date = st.sidebar.date_input("开始日期", datetime.now() - timedelta(days=365))
    end_date = st.sidebar.date_input("结束日期", datetime.now())

else:  # Binance
    ticker = st.sidebar.text_input("输入交易对 (如 BTCUSDT)", value="BTCUSDT")
    interval = st.sidebar.selectbox("时间粒度", ["1d", "4h", "1h", "15m"], index=0)
    limit = st.sidebar.slider("获取 K 线数量", 100, 1000, 500)

# 3. 主界面逻辑
if st.sidebar.button("点击获取数据"):
    with st.spinner('正在获取数据...'):
        df = pd.DataFrame()
        
        # 统一日期格式处理
        sd_str = start_date.strftime('%Y-%m-%d')
        ed_str = end_date.strftime('%Y-%m-%d')

        try:
            if source == "Tiingo (美股/外汇)":
                # 注意：这里我们传递 data_manager 实例作为第一个参数（即 data.py 中的 _self）
                df = data_manager.get_us_stock(data_manager, ticker, sd_str, ed_str)
            elif source == "AKShare (A股历史)":
                # 函数名已对齐为 get_a_stock
                df = data_manager.get_a_stock(data_manager, ticker, sd_str, ed_str)
            elif source == "Binance (加密货币)":
                # 函数名已对齐为 get_crypto
                df = data_manager.get_crypto(data_manager, ticker, interval, limit)

            if df is not None and not df.empty:
                st.success(f"成功获取 {ticker} 数据！")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    fig = go.Figure(data=[go.Candlestick(
                        x=df['Date'], open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='K线'
                    )])
                    fig.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("最新价格")
                    # 显示最后一行数据，美化显示
                    last_price = df.iloc[-1]
                    st.metric("收盘价", f"{last_price['Close']:.2f}")
                    st.dataframe(df.tail(10), use_container_width=True)
            else:
                st.warning("未找到数据，请检查代码或 API 配置。")
                
        except Exception as e:
            st.error(f"发生错误: {e}")
else:
    st.info("👈 请在左侧配置参数并点击按钮。")