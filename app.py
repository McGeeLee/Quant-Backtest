import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data import data_manager
from datetime import datetime

# --- 1. 上下文与引擎 ---
class Context:
    def __init__(self, cash, symbol):
        self.cash = cash
        self.symbol = symbol
        self.portfolio = {symbol: 0}
        self.current_dt = None
        self.current_price = 0
        self.trades = []

class BacktestEngine:
    def run(self, strategy_code, df):
        # 提取配置
        local_scope = {}
        exec(strategy_code, {}, local_scope)
        config = local_scope.get('CONFIG', {})
        
        ctx = Context(config.get('cash', 100000), config.get('ticker', 'AAPL'))
        
        # 定义下单函数
        def order(amount):
            cost = amount * ctx.current_price
            if ctx.cash >= cost:
                ctx.cash -= cost
                ctx.portfolio[ctx.symbol] += amount
                ctx.trades.append({"Date": ctx.current_dt, "Type": "Buy" if amount > 0 else "Sell", 
                                   "Price": ctx.current_price, "Amount": abs(amount)})
                return True
            return False

        # 注入环境
        local_scope.update({'context': ctx, 'order': order, 'pd': pd, 'np': np})
        if 'initialize' in local_scope:
            local_scope['initialize'](ctx)

        history = []
        for i in range(len(df)):
            row = df.iloc[i]
            ctx.current_dt = row['Date']
            ctx.current_price = row['Close']
            
            if 'handle_data' in local_scope:
                local_scope['handle_data'](ctx, df.iloc[:i+1])
            
            total_val = ctx.cash + ctx.portfolio[ctx.symbol] * ctx.current_price
            history.append({"Date": ctx.current_dt, "Equity": total_val, "Price": ctx.current_price})
            
        return pd.DataFrame(history), pd.DataFrame(ctx.trades)

# --- 2. UI 界面 ---
st.set_page_config(page_title="OpenQuant", layout="wide")
st.title("💻 纯代码模式回测平台")

default_code = """CONFIG = {
    "source": "Yahoo", 
    "ticker": "AAPL",
    "start": "2023-01-01",
    "end": "2024-01-01",
    "cash": 100000
}

def initialize(context):
    context.win = 20

def handle_data(context, data):
    if len(data) < context.win: return
    ma = data['Close'].rolling(context.win).mean().iloc[-1]
    price = data['Close'].iloc[-1]
    pos = context.portfolio[context.symbol]
    
    if price > ma and pos == 0: order(100)
    elif price < ma and pos > 0: order(-100)
"""

strategy_text = st.text_area("在代码中修改 CONFIG 即可更改配置", value=default_code, height=400)

if st.button("🚀 执行代码并回测", type="primary"):
    # 预解析配置获取数据
    temp_scope = {}
    exec(strategy_text, {}, temp_scope)
    cfg = temp_scope.get('CONFIG', {})
    
    df = data_manager.get_data(cfg['source'], cfg['ticker'], cfg['start'], cfg['end'])
    
    if not df.empty:
        engine = BacktestEngine()
        history, trades = engine.run(strategy_text, df)
        
        # --- 补全的结果展示区 ---
        st.divider()
        c1, c2 = st.columns([3, 1])
        
        with c1:
            st.subheader("📈 收益曲线")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=history['Date'], y=history['Equity'], name='策略净值', line=dict(color='#1f77b4')))
            # 基准对比
            benchmark = (history['Price'] / history['Price'].iloc[0]) * cfg['cash']
            fig.add_trace(go.Scatter(x=history['Date'], y=benchmark, name='基准收益', line=dict(dash='dash', color='gray')))
            fig.update_layout(hovermode="x unified", height=400, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("📊 核心指标")
            total_ret = (history['Equity'].iloc[-1] / cfg['cash'] - 1) * 100
            st.metric("最终资产", f"${history['Equity'].iloc[-1]:,.2f}")
            st.metric("累计收益率", f"{total_ret:.2f}%")
            st.write(f"交易次数: {len(trades)}")

        if not trades.empty:
            with st.expander("📝 交易明细"):
                st.dataframe(trades, use_container_width=True)
    else:
        st.error("数据加载失败，请检查配置。")