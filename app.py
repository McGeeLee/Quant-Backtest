import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data import data_manager  # 引用你之前的 data.py
from datetime import datetime

# --- 核心引擎：增加配置提取功能 ---
class BacktestEngine:
    def __init__(self):
        self.cash = 100000.0
        self.portfolio = {}
        self.history = []
        self.trades = []

    def get_strategy_config(self, strategy_code):
        """预运行代码，提取 CONFIG 字典"""
        local_scope = {}
        try:
            exec(strategy_code, {}, local_scope)
            return local_scope.get('CONFIG', {})
        except:
            return {}

    def run(self, symbol, df, strategy_code):
        # ... (此处逻辑同上一版，保持 Context 和 Event Loop 不变)
        # 为节省篇幅，核心逻辑参考上一版 app.py 的 run 函数
        pass

# --- Streamlit UI ---
st.set_page_config(page_title="OpenQuant Code-Mode", layout="wide")

st.title("💻 纯代码模式回测平台")

# 默认代码模板：直接在里面写配置
default_code = """# --- 1. 配置区域 ---
CONFIG = {
    "source": "Yahoo",        # 数据源: Tushare, Yahoo, Tiingo
    "ticker": "AAPL",         # 股票代码
    "start": "2023-01-01",    # 开始日期
    "end": "2024-01-01",      # 结束日期
    "cash": 100000            # 初始资金
}

# --- 2. 策略逻辑 ---
def initialize(context):
    context.win = 20

def handle_data(context, data):
    ma = data['Close'].rolling(window=context.win).mean().iloc[-1]
    price = data['Close'].iloc[-1]
    curr_pos = context.portfolio.get(context.symbol, 0)
    
    if price > ma and curr_pos == 0:
        order(100)
    elif price < ma and curr_pos > 0:
        order(-100)
"""

# 单操作台布局
strategy_text = st.text_area("在代码中修改 CONFIG 即可更改配置", value=default_code, height=500)

if st.button("🚀 执行代码并回测", type="primary"):
    engine = BacktestEngine()
    
    # 第一步：提取配置
    config = engine.get_strategy_config(strategy_text)
    source = config.get("source", "Yahoo")
    ticker = config.get("ticker", "AAPL")
    start = config.get("start", "2023-01-01")
    end = config.get("end", "2024-01-01")

    # 第二步：获取数据
    with st.spinner(f"正在从 {source} 获取 {ticker} 数据..."):
        df = data_manager.get_data(source, ticker, start, end)

    if not df.empty:
        # 第三步：运行回测（逻辑同前）
        # ... 执行引擎并绘图
        st.success(f"回测完成：{ticker} ({start} 至 {end})")
        # (此处补全绘图逻辑即可)
    else:
        st.error("无法获取数据，请检查 CONFIG 中的代码格式或日期。")