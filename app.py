import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import data_manager  # 导入我们在 data.py 中定义的实例
from datetime import datetime, timedelta

# 1. 页面基本配置
st.set_page_config(page_title="量化交易平台 - 数据测试", layout="wide")

st.title("📊 量化平台数据源验证")

# 2. 侧边栏：配置参数
st.sidebar.header("数据查询配置")

# 选择数据源
source = st.sidebar.selectbox(
    "选择数据源",
    ["Tiingo (美股/外汇)", "AKShare (A股历史)", "Binance (加密货币)"]
)

# 根据数据源动态调整输入框
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

# 3. 主界面逻辑：获取并展示数据
if st.sidebar.button("点击获取数据"):
    with st.spinner('正在从 API 获取数据...'):
        df = pd.DataFrame()
        
        # 转换日期格式为字符串，匹配 data.py 的接口需求
        sd_str = start_date.strftime('%Y%m%d') if "AK" in source else start_date.strftime('%Y-%m-%d')
        ed_str = end_date.strftime('%Y%m%d') if "AK" in source else end_date.strftime('%Y-%m-%d')

        try:
            if source == "Tiingo (美股/外汇)":
                df = data_manager.get_us_stock(ticker, sd_str, ed_str)
            elif source == "AKShare (A股历史)":
                df = data_manager.get_a_stock_ak(ticker, sd_str, ed_str)
            elif source == "Binance (加密货币)":
                df = data_manager.get_crypto_binance(ticker, interval, limit)

            if not df.empty:
                st.success(f"成功获取 {ticker} 数据！")
                
                # 分两栏展示：左边是图表，右边是原始数据
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("价格趋势 (K线/线图)")
                    fig = go.Figure(data=[go.Candlestick(
                        x=df['Date'],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='K线'
                    )])
                    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("最新数据样本")
                    st.dataframe(df.tail(15), use_container_width=True)
                    
                # 基础统计信息
                st.divider()
                st.subheader("数据统计摘要")
                st.write(df.describe())
            else:
                st.error("未能获取到数据，请检查 API Key 或网络。")
                
        except Exception as e:
            st.error(f"发生错误: {e}")

else:
    st.info("👈 请在左侧配置参数，然后点击'点击获取数据'按钮。")

# 4. 页脚提示
st.sidebar.markdown("---")
st.sidebar.caption("提示：请确保已经在 `.streamlit/secrets.toml` 中配置了 API Key。")