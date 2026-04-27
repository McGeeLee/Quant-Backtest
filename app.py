import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data import data_manager
from datetime import datetime

# --- 1. 核心回测引擎 ---
class Context:
    def __init__(self, cash, symbol):
        self.cash = cash
        self.symbol = symbol
        self.portfolio = {symbol: 0}
        self.current_dt = None
        self.current_price = 0
        self.trades = []

class BacktestEngine:
    def run(self, strategy_code, main_df, benchmark_df, initial_cash, ticker):
        # 初始化上下文
        ctx = Context(initial_cash, ticker)
        
        # 定义下单函数
        def order(amount):
            cost = amount * ctx.current_price
            if ctx.cash >= cost:
                ctx.cash -= cost
                ctx.portfolio[ctx.symbol] += amount
                ctx.trades.append({
                    "时间": ctx.current_dt, 
                    "类型": "买入" if amount > 0 else "卖出", 
                    "成交价": round(ctx.current_price, 2), 
                    "数量": abs(amount)
                })
                return True
            return False

        # 构建执行环境
        global_env = {
            'context': ctx,
            'order': order,
            'pd': pd,
            'np': np,
            '__builtins__': __builtins__
        }
        
        # 执行策略定义
        exec(strategy_code, global_env)
        if 'initialize' in global_env:
            global_env['initialize'](ctx)

        history = []
        # 以主标的数据集为时间轴
        for i in range(len(main_df)):
            row = main_df.iloc[i]
            current_date = row['Date']
            ctx.current_dt = current_date
            ctx.current_price = row['Close']
            
            # 执行每日策略逻辑
            if 'handle_data' in global_env:
                global_env['handle_data'](ctx, main_df.iloc[:i+1])
            
            # 获取当天的基准价格 (如果基准数据缺失则取最近值)
            b_price_row = benchmark_df[benchmark_df['Date'] <= current_date]
            b_price = b_price_row.iloc[-1]['Close'] if not b_price_row.empty else benchmark_df.iloc[0]['Close']
            
            # 记录资产净值
            total_val = ctx.cash + ctx.portfolio[ctx.symbol] * ctx.current_price
            history.append({
                "Date": current_date, 
                "Equity": total_val, 
                "Price": ctx.current_price,
                "Benchmark_Price": b_price
            })
            
        return pd.DataFrame(history), pd.DataFrame(ctx.trades)

# --- 2. Streamlit UI 界面 ---
st.set_page_config(page_title="OpenQuant V2", layout="wide")
st.title("🚀 开放量化回测平台 (自定义基准版)")

# 默认代码模板：包含自定义基准 CONFIG
default_code = """# --- 1. 配置区域 ---
CONFIG = {
    "source": "Yahoo",        # 数据源: Tushare, Yahoo, Tiingo
    "ticker": "AAPL",         # 交易标的
    "benchmark": "SPY",       # 基准标的 (美股选SPY/QQQ, A股选000300.SS)
    "start": "2023-01-01",
    "end": "2024-01-01",
    "cash": 100000
}

# --- 2. 策略逻辑 ---
def initialize(context):
    context.win = 20

def handle_data(context, data):
    if len(data) < context.win: return
    
    ma = data['Close'].rolling(context.win).mean().iloc[-1]
    price = data['Close'].iloc[-1]
    pos = context.portfolio[context.symbol]
    
    # 策略示例：价格站上均线全仓买入，跌破全仓卖出
    if price > ma and pos == 0:
        amount = int(context.cash / price)
        order(amount)
    elif price < ma and pos > 0:
        order(-pos)
"""

strategy_text = st.text_area("在下方 CONFIG 中修改配置及策略逻辑", value=default_code, height=450)

if st.button("开始回测", type="primary"):
    try:
        # 预解析 CONFIG
        pre_env = {}
        exec(strategy_text, pre_env)
        cfg = pre_env.get('CONFIG', {})
        
        with st.spinner(f"正在同步获取 {cfg['ticker']} 和基准 {cfg['benchmark']} 的数据..."):
            # 获取主标的数据
            main_df = data_manager.get_data(cfg['source'], cfg['ticker'], cfg['start'], cfg['end'])
            # 获取基准标的数据
            bench_df = data_manager.get_data(cfg['source'], cfg['benchmark'], cfg['start'], cfg['end'])
            
            if not main_df.empty and not bench_df.empty:
                engine = BacktestEngine()
                history, trades = engine.run(strategy_text, main_df, bench_df, cfg['cash'], cfg['ticker'])
                
                # --- 结果展示 ---
                st.divider()
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    st.subheader("📈 累计收益对比")
                    fig = go.Figure()
                    # 策略曲线
                    fig.add_trace(go.Scatter(x=history['Date'], y=history['Equity'], name='我的策略', line=dict(color='#1f77b4', width=2)))
                    # 自定义基准曲线 (归一化计算)
                    b_start_price = history['Benchmark_Price'].iloc[0]
                    history['Benchmark_Equity'] = (history['Benchmark_Price'] / b_start_price) * cfg['cash']
                    fig.add_trace(go.Scatter(x=history['Date'], y=history['Benchmark_Equity'], name=f"基准: {cfg['benchmark']}", line=dict(dash='dash', color='gray')))
                    
                    fig.update_layout(hovermode="x unified", height=450, margin=dict(l=0,r=0,t=20,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                with c2:
                    st.subheader("📊 统计指标")
                    final_val = history['Equity'].iloc[-1]
                    total_ret = (final_val / cfg['cash'] - 1) * 100
                    bench_ret = (history['Benchmark_Equity'].iloc[-1] / cfg['cash'] - 1) * 100
                    
                    st.metric("策略最终资产", f"${final_val:,.2f}")
                    st.metric("策略累计收益", f"{total_ret:.2f}%", delta=f"{total_ret - bench_ret:.2f}% (相对基准)")
                    st.metric("基准累计收益", f"{bench_ret:.2f}%")
                    st.write(f"总交易次数: {len(trades)}")

                if not trades.empty:
                    with st.expander("📝 历史交易记录"):
                        st.dataframe(trades, use_container_width=True)
            else:
                st.error("数据加载失败。请确保交易标的和基准标的代码正确，且在同一时间段内有数据。")
    except Exception as e:
        st.error(f"回测过程中发生错误: {e}")