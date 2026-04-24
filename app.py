import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Professional Backtest", layout="wide")

# 侧边栏：参数配置
st.sidebar.title("🛠️ 策略配置")
symbol = st.sidebar.text_input("代码", "NVDA")
initial_cash = st.sidebar.number_input("初始资金", value=100000)
fee = st.sidebar.slider("手续费 (%)", 0.0, 0.5, 0.1) / 100

# 主界面
st.title("📈 专业级策略回测平台")

if st.sidebar.button("开始回测"):
    fetcher = DataFetcher()
    data = fetcher.fetch(symbol, "2023-01-01", "2024-01-01")
    
    # 运行策略
    results = StrategyLibrary.perfect_prediction(data, fee)
    
    # 计算评价指标
    engine = BacktestEngine(initial_cash)
    metrics = engine.calculate_performance(results['equity'])
    
    # 布局：上方显示指标
    col1, col2, col3 = st.columns(3)
    col1.metric("累计收益", f"{metrics['Total Return']:.2%}")
    col2.metric("最大回撤", f"{metrics['Max Drawdown']:.2%}")
    col3.metric("夏普比率", f"{metrics['Sharpe Ratio']:.2f}")
    
    # 中间：绘制交互式净值曲线 (Plotly)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['datetime'], y=results['equity'], name='策略净值'))
    fig.update_layout(title="收益增长曲线 (Log Scale)", yaxis_type="log")
    st.plotly_chart(fig, use_container_width=True)
    
    # 下方：数据详情
    with st.expander("查看交易明细"):
        st.dataframe(results)