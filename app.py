import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import data_manager  
from datetime import datetime, timedelta

# 1. 页面基本配置
st.set_page_config(
    page_title="Gemini Quant - 智能量化测试平台",
    page_icon="📈",
    layout="wide"
)

# 简单的 CSS 美化
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 量化平台数据源验证系统")
st.caption("基于 Streamlit + Tiingo/AKShare/Binance 多源数据集成")

# 2. 侧边栏：配置参数
st.sidebar.header("⚙️ 数据查询配置")

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

st.sidebar.divider()

# 3. 主界面逻辑
if st.sidebar.button("🚀 点击获取并测试数据"):
    with st.spinner('正在从远程 API 调取数据，请稍候...'):
        df = pd.DataFrame()
        
        # 统一日期格式处理
        sd_str = start_date.strftime('%Y-%m-%d') if "Binance" not in source else ""
        ed_str = end_date.strftime('%Y-%m-%d') if "Binance" not in source else ""

        try:
            # 调用 data.py 中 data_manager 实例的方法
            if source == "Tiingo (美股/外汇)":
                df = data_manager.get_us_stock(ticker, sd_str, ed_str)
            elif source == "AKShare (A股历史)":
                df = data_manager.get_a_stock(ticker, sd_str, ed_str)
            elif source == "Binance (加密货币)":
                df = data_manager.get_crypto(ticker, interval, limit)

            if df is not None and not df.empty:
                st.success(f"✅ 成功获取 {ticker} 数据！共计 {len(df)} 条记录。")
                
                # --- 第一行：指标卡片 ---
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2] if len(df) > 1 else last_row
                change = last_row['Close'] - prev_row['Close']
                change_pct = (change / prev_row['Close']) * 100

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("当前价格", f"{last_row['Close']:.2f}")
                m2.metric("涨跌幅", f"{change:.2f}", f"{change_pct:.2f}%")
                m3.metric("最高价", f"{last_row['High']:.2f}")
                m4.metric("成交量", f"{last_row['Volume']:.0f}")

                # --- 第二行：图表与表格 ---
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader("K 线趋势图")
                    fig = go.Figure(data=[go.Candlestick(
                        x=df['Date'],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='OHLC',
                        increasing_line_color= '#ef5350', # 习惯性红色上涨
                        decreasing_line_color= '#26a69a'  # 习惯性绿色下跌
                    )])
                    fig.update_layout(
                        xaxis_rangeslider_visible=False, 
                        height=600,
                        template="plotly_white",
                        margin=dict(l=10, r=10, t=10, b=10)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("原始数据样本")
                    st.dataframe(
                        df.tail(20).sort_values(by='Date', ascending=False), 
                        use_container_width=True,
                        height=550
                    )
                
                # --- 第三行：数据统计 ---
                with st.expander("查看描述性统计分析"):
                    st.write(df.describe())
                    
            else:
                st.warning("⚠️ 接口返回数据为空。请检查：1. Ticker 是否正确 2. API Key 是否在 Secrets 中配置 3. 网络是否通畅。")
                
        except Exception as e:
            st.error(f"❌ 程序运行出错: {e}")
else:
    # 初始状态下的欢迎语
    st.info("💡 请在左侧侧边栏配置参数，然后点击按钮开始测试数据流。")
    
    # 展示一个示例布局
    c1, c2, c3 = st.columns(3)
    c1.info("**Tiingo**: 需 API Key，适合美股精细化回测。")
    c2.success("**AKShare**: 无需 Key，A 股数据最全。")
    c3.warning("**Binance**: 加密货币首选，支持分钟级数据。")

# 4. 页脚
st.sidebar.markdown("---")
st.sidebar.caption("Gemini Quant Framework v1.0")