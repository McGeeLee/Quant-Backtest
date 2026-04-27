import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data import data_manager  # 导入你的 DataManager 实例

# --- 核心回测引擎 ---
class BacktestEngine:
    def __init__(self, initial_cash=100000.0):
        self.cash = initial_cash
        self.portfolio = {}  # {symbol: quantity}
        self.history = []
        self.trades = []

    def run(self, symbol, df, strategy_code):
        # 初始化沙盒环境
        context = type('Context', (), {
            'cash': self.cash,
            'portfolio': self.portfolio,
            'current_price': 0,
            'current_dt': None,
            'symbol': symbol
        })
        
        # 内部下单函数映射给用户
        def order(amount):
            cost = amount * context.current_price
            if context.cash >= cost:
                context.cash -= cost
                context.portfolio[symbol] = context.portfolio.get(symbol, 0) + amount
                self.trades.append({
                    "时间": context.current_dt,
                    "类型": "买入" if amount > 0 else "卖出",
                    "数量": abs(amount),
                    "价格": f"{context.current_price:.2f}"
                })
                return True
            return False

        # 准备执行环境
        local_scope = {
            'context': context,
            'order': order,
            'pd': pd,
            'np': np
        }

        try:
            exec(strategy_code, {}, local_scope)
            if 'initialize' in local_scope:
                local_scope['initialize'](context)
            
            # 时间序列模拟
            for i in range(len(df)):
                row = df.iloc[i]
                context.current_dt = row['Date']
                context.current_price = row['Close']
                
                # 喂给 handle_data 的历史数据（避免未来函数）
                data_slice = df.iloc[:i+1]
                
                if 'handle_data' in local_scope:
                    local_scope['handle_data'](context, data_slice)
                
                # 计算净值
                pos_val = context.portfolio.get(symbol, 0) * context.current_price
                self.history.append({
                    "Date": context.current_dt,
                    "Equity": context.cash + pos_val,
                    "Benchmark": (row['Close'] / df.iloc[0]['Close']) * self.cash
                })
            
            return pd.DataFrame(self.history), pd.DataFrame(self.trades)
        except Exception as e:
            st.error(f"策略执行报错: {e}")
            return None, None

# --- Streamlit UI 布局 ---
st.set_page_config(page_title="JoinQuant Lite", layout="wide")

st.sidebar.title("🛠 配置面板")
source = st.sidebar.selectbox("数据源", ["Yahoo", "Tushare", "Tiingo"])
ticker = st.sidebar.text_input("代码 (例如: AAPL 或 000001.SZ)", "AAPL")
start_date = st.sidebar.date_input("开始日期", datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("结束日期", datetime.now())

# 1. 获取数据
with st.spinner("正在获取数据..."):
    df = data_manager.get_data(source, ticker, str(start_date), str(end_date))

if df.empty:
    st.warning("⚠️ 未获取到数据，请检查 Token 配置或代码是否正确。")
else:
    st.success(f"✅ 成功加载 {len(df)} 条记录")

    col_code, col_res = st.columns([1, 1])

    with col_code:
        st.subheader("📝 编写策略")
        default_code = """def initialize(context):
    context.win = 20

def handle_data(context, data):
    if len(data) < context.win:
        return
        
    # 计算移动平均线
    ma = data['Close'].rolling(window=context.win).mean().iloc[-1]
    price = data['Close'].iloc[-1]
    curr_pos = context.portfolio.get(context.symbol, 0)
    
    # 策略逻辑
    if price > ma and curr_pos == 0:
        order(100)  # 买入 100 股
    elif price < ma and curr_pos > 0:
        order(-100) # 卖出 100 股
"""
        strategy_text = st.text_area("Python 代码区", value=default_code, height=450)
        run_backtest = st.button("🚀 运行回测", type="primary", use_container_width=True)

    with col_res:
        st.subheader("📊 回测报告")
        if run_backtest:
            engine = BacktestEngine()
            history, trades = engine.run(ticker, df, strategy_text)
            
            if history is not None:
                # 绘制收益曲线
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=history['Date'], y=history['Equity'], name='策略净值'))
                fig.add_trace(go.Scatter(x=history['Date'], y=history['Benchmark'], name='基准收益', line=dict(dash='dash')))
                fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), height=350, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
                # 计算关键指标
                total_ret = (history['Equity'].iloc[-1] / history['Equity'].iloc[0] - 1) * 100
                st.metric("累计收益率", f"{total_ret:.2f}%")
                
                with st.expander("查看成交明细"):
                    st.dataframe(trades, use_container_width=True)