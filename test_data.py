import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
# 假设你已经把上一轮生成的 UniversalDataHub 类保存到了 data_hub.py 中
from data import UniversalDataHub 

st.set_page_config(page_title="数据中心字段对齐测试", layout="wide")

st.title("📊 UniversalDataHub 字段整齐度测试")

# 请在这里填入你的 Tushare Token
TUSHARE_TOKEN = "765e94535372b39b7790739a2ba7400db7c4e35a93b333dbd6b5a231" 

# 1. 初始化数据中心
hub = UniversalDataHub(tushare_token=TUSHARE_TOKEN)

# 2. 定义测试用例
test_cases = [
    {"name": "加密货币 (Yahoo)", "symbol": "BTC-USD"},
    {"name": "美股 (Yahoo)", "symbol": "AAPL"},
    {"name": "A股 (Tushare)", "symbol": "000001.SZ"}
]

start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
end_date = datetime.now().strftime('%Y%m%d')

st.info(f"测试区间: {start_date} 至 {end_date}")

# 3. 循环执行测试
for case in test_cases:
    st.subheader(f"测试目标: {case['name']} - `{case['symbol']}`")
    
    with st.spinner(f"正在抓取 {case['symbol']}..."):
        df = hub.get_data(case['symbol'], start_date, end_date)
        
    if not df.empty:
        # 字段检查逻辑
        expected_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
        actual_cols = df.columns.tolist()
        is_tidy = set(expected_cols) == set(actual_cols)
        
        # UI 展示
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if is_tidy:
                st.success("✅ 字段完全整齐")
            else:
                st.error(f"❌ 字段缺失或冗余: {actual_cols}")
            
            st.write("**字段列表:**")
            st.code(str(actual_cols))
            
            st.write("**索引类型:**")
            st.code(str(df.index.dtype))
            
        with col2:
            st.write("**df.head(3) 数据预览:**")
            st.dataframe(df.head(3), use_container_width=True)
            
    else:
        st.error(f"未能获取到 `{case['symbol']}` 的数据，请检查网络或 Token。")
    
    st.divider()

st.balloons()