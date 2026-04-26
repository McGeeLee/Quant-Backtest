import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import data_manager  # 确保 data.py 与此文件在同一目录
from datetime import datetime, timedelta

# 1. 页面基本配置
st.set_page_config(
    page_title="Gemini Quant - 全源测试终端",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 量化数据引擎 - 最终整合测试")
st.caption("集成 Tushare / AKShare / Binance / Tiingo / Yahoo 多重保底系统")

# 2. 侧边栏：配置参数
st.sidebar.header("⚙️ 数据源配置")

# 定义数据源映射，方便 UI 显示与后台逻辑对应
SOURCE_MAP = {
    "AKShare (A股 - 含保底)": "AKShare",
    "Tushare (A股 - 专业级)": "Tushare",
    "Binance (加密货币 - 含保底)": "Binance",
    "Tiingo (美股 - 需Key)": "Tiingo",
    "Yahoo Finance (直连)": "Yahoo"
}

source_label = st.sidebar.selectbox("选择数据源", list(SOURCE_MAP.keys()))
source_type = SOURCE_MAP[source_label]

# 动态调整输入框
ticker = "600519"  # 默认值
if source_type == "Tushare":
    ticker = st.sidebar.text_input("代码 (需后缀, 如 600519.SH)", value="600519.SH")
elif source_type == "Yahoo":
    ticker = st.sidebar.text_input("代码 (Yahoo格式, 如 AAPL 或 600519.SS)", value="AAPL")
elif source_type == "Binance":
    ticker = st.sidebar.text_input("交易对 (如 BTCUSDT)", value="BTCUSDT")
else:
    ticker = st.sidebar.text_input("输入代码", value="600519")

# 时间选择
start_date = st.sidebar.date_input("开始日期", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("结束日期", datetime.now())

# 加密货币专用配置
kwargs = {}
if source_type == "Binance":
    kwargs['interval'] = st.sidebar.selectbox("粒度", ["1d", "4h", "1h"], index=0)
    kwargs['limit'] = st.sidebar.slider("数量", 100, 1000, 500)

st.sidebar.divider()

# 3. 执行测试
if st.sidebar.button("运行测试"):
    with st.spinner(f'正在通过 {source_type} 获取数据...'):
        sd_str = start_date.strftime('%Y-%m-%d')
        ed_str = end_date.strftime('%Y-%m-%d')

        # 调用合并后的统一接口
        df = data_manager.get_data(source_type, ticker, sd_str, ed_str, **kwargs)

        if df is not None and not df.empty:
            st.success(f"✅ 获取成功！来源: {source_type} | 记录数: {len(df)}")
            
            # --- 布局：指标卡 ---
            last_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) > 1 else last_price
            delta = last_price - prev_price
            
            c1, c2, c3 = st.columns(3)
            c1.metric("最新价格", f"{last_price:.2f}")
            c2.metric("涨跌幅", f"{delta:.2f}", f"{(delta/prev_price)*100:.2f}%")
            c3.metric("数据跨度", f"{len(df)} 天/条")

            # --- 布局：图表 ---
            fig = go.Figure(data=[go.Candlestick(
                x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#ef5350', decreasing_line_color='#26a69a'
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- 布局：详情 ---
            with st.expander("查看原始数据 (最后10行)"):
                st.table(df.tail(10))
        else:
            st.error("❌ 未能获取数据。请检查代码格式、API Key 或网络连接。")
            if source_type == "Tushare":
                st.info("提示：Tushare 需要在 Secrets 中配置 TUSHARE_TOKEN。")

# 4. 环境说明
st.sidebar.caption("DataManager v2.0 (Integrated)")