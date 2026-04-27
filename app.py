import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. 核心上下文与账户管理 ---
class Context:
    def __init__(self, cash=100000.0):
        self.cash = cash
        self.portfolio = {}  # {symbol: quantity}
        self.history = []    # 记录净值变化
        self.trades = []     # 记录交易流水
        self.current_dt = None
        self.current_price = 0.0

    def order(self, symbol, amount):
        cost = amount * self.current_price
        if self.cash >= cost:
            self.cash -= cost
            self.portfolio[symbol] = self.portfolio.get(symbol, 0) + amount
            self.trades.append({
                "date": self.current_dt,
                "type": "Buy" if amount > 0 else "Sell",
                "amount": abs(amount),
                "price": self.current_price
            })
            return True
        return False

    @property
    def total_value(self):
        # 简化版：目前只支持单标的回测
        pos_value = sum(qty * self.current_price for qty, pos in self.portfolio.items())
        return self.cash + pos_value

# --- 2. 回测引擎 ---
def run_backtest(strategy_code, df):
    ctx = Context()
    # 定义沙盒环境，限制危险函数
    safe_globals = {
        "context": ctx,
        "pd": pd,
        "np": np,
        "print": print
    }
    
    try:
        # 1. 动态执行策略定义
        exec(strategy_code, safe_globals)
        
        # 2. 初始化
        if "initialize" in safe_globals:
            safe_globals["initialize"](ctx)
        
        # 3. 步进模拟 (Event Loop)
        for i in range(len(df)):
            row = df.iloc[i]
            ctx.current_dt = row['Date']
            ctx.current_price = row['Close']
            
            # 提供给 handle_data 的历史切片（防止未来函数）
            data_slice = df.iloc[:i+1]
            
            if "handle_data" in safe_globals:
                safe_globals["handle_data"](ctx, data_slice)
            
            # 记录每日净值
            ctx.history.append({
                "Date": ctx.current_dt,
                "Equity": ctx.total_value,
                "Benchmark": (row['Close'] / df.iloc[0]['Close']) * 100000.0
            })
            
        return pd.DataFrame(ctx.history), pd.DataFrame(ctx.trades)
    except Exception as e:
        st.error(f"策略运行错误: {e}")
        return None, None

# --- 3. Streamlit UI 界面 ---
st.set_page_config(page_title="OpenQuant", layout="wide")

st.title("🚀 OpenQuant 极简回测平台")
st.sidebar.header("配置与参数")

# 模拟数据生成 (实际部署可接入你之前的 DataManager)
@st.cache_data
def get_mock_data():
    dates = pd.date_range(start="2023-01-01", periods=200)
    prices = 100 + np.cumsum(np.random.randn(200) * 2)
    return pd.DataFrame({"Date": dates, "Close": prices, "Open": prices*0.99, "High": prices*1.01, "Low": prices*0.98})

df = get_mock_data()

# 策略编辑器
default_code = """# 初始化函数
def initialize(context):
    context.symbol = "Stock_A"
    context.window = 20

# 每日处理逻辑
def handle_data(context, data):
    if len(data) < context.window:
        return
    
    # 简单的均线策略
    ma = data['Close'].tail(context.window).mean()
    current_price = data['Close'].iloc[-1]
    
    # 金叉买入 (持仓为0时)
    if current_price > ma and context.portfolio.get(context.symbol, 0) == 0:
        context.order(context.symbol, 100)
    # 死叉卖出 (有持仓时)
    elif current_price < ma and context.portfolio.get(context.symbol, 0) > 0:
        context.order(context.symbol, -100)
"""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("编写策略")
    code = st.text_area("Python 策略代码 (支持 initialize 和 handle_data)", value=default_code, height=400)
    btn_run = st.button("开始回测", type="primary")

# 执行逻辑
if btn_run:
    with st.spinner('计算中...'):
        history_df, trades_df = run_backtest(code, df)
        
        if history_df is not None:
            with col2:
                st.subheader("回测结果")
                # 绘制净值曲线
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=history_df['Date'], y=history_df['Equity'], name='策略净值'))
                fig.add_trace(go.Scatter(x=history_df['Date'], y=history_df['Benchmark'], name='基准收益', line=dict(dash='dash')))
                st.plotly_chart(fig, use_container_width=True)
                
                # 计算指标
                total_return = (history_df['Equity'].iloc[-1] / 100000.0 - 1) * 100
                st.metric("累计收益率", f"{total_return:.2f}%")
                
                # 交易明细
                with st.expander("查看交易明细"):
                    st.table(trades_df)