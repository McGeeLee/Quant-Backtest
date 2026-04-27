import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data import data_manager
from datetime import datetime

# --- 1. 环境定义 ---
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
        pre_scope = {}
        exec(strategy_code, pre_scope)
        config = pre_scope.get('CONFIG', {})
        
        ctx = Context(config.get('cash', 100000), config.get('ticker', 'AAPL'))
        
        # 定义下单函数
        def order(amount):
            cost = amount * ctx.current_price
            if ctx.cash >= cost:
                ctx.cash -= cost
                ctx.portfolio[ctx.symbol] += amount
                ctx.trades.append({
                    "Date": ctx.current_dt, 
                    "Type": "Buy" if amount > 0 else "Sell", 
                    "Price": round(ctx.current_price, 2), 
                    "Amount": abs(amount)
                })
                return True
            return False

        # --- 核心修复：构建一个统一的作用域 ---
        # 把 context 和 order 放到全局域，确保 handle_data 能看到它们
        global_env = {
            'context': ctx,
            'order': order,
            'pd': pd,
            'np': np,
            '__builtins__': __builtins__ # 允许使用内置函数
        }
        
        # 在这个环境下执行完整的用户代码
        exec(strategy_code, global_env)
        
        if 'initialize' in global_env:
            global_env['initialize'](ctx)

        history = []
        for i in range(len(df)):
            row = df.iloc[i]
            ctx.current_dt = row['Date']
            ctx.current_price = row['Close']
            
            if 'handle_data' in global_env:
                # 传入当前时刻之前的切片
                global_env['handle_data'](ctx, df.iloc[:i+1])
            
            total_val = ctx.cash + ctx.portfolio[ctx.symbol] * ctx.current_price
            history.append({
                "Date": ctx.current_dt, 
                "Equity": total_val, 
                "Price": ctx.current_price
            })
            
        return pd.DataFrame(history), pd.DataFrame(ctx.trades)

# --- 2. Streamlit UI ---
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
    if len(data) < context.win:
        return
        
    # 计算移动平均线
    ma = data['Close'].rolling(window=context.win).mean().iloc[-1]
    price = data['Close'].iloc[-1]
    pos = context.portfolio[context.symbol]
    
    # 策略逻辑
    if price > ma and pos == 0:
        order(100)
    elif price < ma and pos > 0:
        order(-100)
"""

strategy_text = st.text_area("在代码中修改 CONFIG 即可更改配置", value=default_code, height=400)

if st.button("🚀 执行代码并回测", type="primary"):
    try:
        # 获取配置
        pre_env = {}
        exec(strategy_text, pre_env)
        cfg = pre_env.get('CONFIG', {})
        
        with st.spinner("获取数据并回测中..."):
            df = data_manager.get_data(cfg['source'], cfg['ticker'], cfg['start'], cfg['end'])
            
            if not df.empty:
                engine = BacktestEngine()
                history, trades = engine.run(strategy_text, df)
                
                # --- 结果展示 ---
                st.divider()
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    st.subheader("📈 收益曲线")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=history['Date'], y=history['Equity'], name='策略净值'))
                    benchmark = (history['Price'] / history['Price'].iloc[0]) * cfg['cash']
                    fig.add_trace(go.Scatter(x=history['Date'], y=benchmark, name='基准收益', line=dict(dash='dash', color='gray')))
                    fig.update_layout(hovermode="x unified", margin=dict(l=0,r=0,t=20,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                with c2:
                    st.subheader("📊 核心指标")
                    final_equity = history['Equity'].iloc[-1]
                    total_ret = (final_equity / cfg['cash'] - 1) * 100
                    st.metric("最终资产", f"${final_equity:,.2f}")
                    st.metric("累计收益率", f"{total_ret:.2f}%", delta=f"{total_ret:.2f}%")
                    st.write(f"总交易笔数: {len(trades)}")

                if not trades.empty:
                    with st.expander("📝 交易明细"):
                        st.dataframe(trades, use_container_width=True)
            else:
                st.error("数据加载为空，请检查代码后缀（如 .SZ）或日期范围。")
    except Exception as e:
        st.error(f"发生错误: {e}")