import pandas as pd
import tushare as ts
import yfinance as yf
import akshare as ak
import streamlit as st
from datetime import datetime

class UniversalDataHub:
    def __init__(self, tushare_token=None):
        """
        初始化数据中心，配置Tushare Token
        """
        self.token = "765e94535372b39b7790739a2ba7400db7c4e35a93b333dbd6b5a231"
        if tushare_token:
            ts.set_token(tushare_token)
            self.pro = ts.pro_api()

    def detect_asset_and_source(self, symbol: str):
        """
        识别资产类型并路由到最佳数据源
        """
        symbol = symbol.upper()

        # 1. 加密货币 (Crypto) -> Yahoo
        if "-USD" in symbol:
            return "crypto", "yahoo"

        # 2. 港股 (HK) -> Tushare 或 Yahoo
        if symbol.endswith(".HK"):
            return "hk_stock", "tushare"

        # 3. A股 (Stock/ETF) -> Tushare
        if symbol.endswith((".SH", ".SZ")):
            code = symbol.split(".")[0]
            if code.startswith("51"):
                return "etf", "tushare"
            return "a_stock", "tushare"

        # 4. 默认美股等 -> Yahoo
        return "us_stock", "yahoo"

    def _format_date(self, date_obj_or_str, target_format="%Y%m%d"):
        """
        统一日期格式转换
        """
        if isinstance(date_obj_or_str, (datetime, pd.Timestamp)):
            return date_obj_or_str.strftime(target_format)
        
        # 处理 2025-01-01 -> 20250101 等情况
        clean_date = str(date_obj_or_str).replace("-", "").replace("/", "")
        if target_format == "%Y-%m-%d" and len(clean_date) == 8:
            return f"{clean_date[:4]}-{clean_date[4:6]}-{clean_date[6:]}"
        return clean_date

    def _standardize_df(self, df, source):
        """
        强制对齐列名为：open, high, low, close, volume, amount
        并将索引设为 datetime
        """
        if df is None or df.empty:
            return pd.DataFrame()

        # 处理 Yahoo 的 MultiIndex 坑
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if col[1] == '' else col[1] for col in df.columns]

        # 定义原始数据源到标准字段的映射
        maps = {
            "tushare": {
                'trade_date': 'datetime', 'vol': 'volume', 'amount': 'amount',
                'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'
            },
            "yahoo": {
                'Date': 'datetime', 'Open': 'open', 'High': 'high', 
                'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            },
            "akshare": {
                '日期': 'datetime', '开盘': 'open', '最高': 'high', 
                '最低': 'low', '收盘': 'close', '成交量': 'volume', '成交额': 'amount'
            }
        }

        current_map = maps.get(source, {})
        df = df.rename(columns=current_map)

        # 确保有 datetime 列并设为索引
        if 'datetime' not in df.columns and df.index.name != 'datetime':
            df = df.reset_index().rename(columns={'index': 'datetime', 'Date': 'datetime'})

        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

        # 强制小写列名并补齐
        df.columns = [c.lower() for c in df.columns]
        standard_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in standard_cols:
            if col not in df.columns:
                df[col] = 0.0 # 缺失字段补0

        return df[standard_cols].sort_index()

    @st.cache_data(ttl=3600)
    def get_data(_self, symbol: str, start: str, end: str):
        """
        主查询接口，支持多源切换与异常处理
        """
        asset_type, source = _self.detect_asset_and_source(symbol)
        
        # 准备不同格式的日期
        ts_start = _self._format_date(start, "%Y%m%d")
        ts_end = _self._format_date(end, "%Y%m%d")
        yf_start = _self._format_date(start, "%Y-%m-%d")
        yf_end = _self._format_date(end, "%Y-%m-%d")

        df = pd.DataFrame()

        try:
            # --- 1. Tushare 路径 ---
            if source == "tushare" and _self.token:
                if asset_type == "a_stock":
                    df = _self.pro.daily(ts_code=symbol, start_date=ts_start, end_date=ts_end)
                elif asset_type == "etf":
                    df = _self.pro.fund_daily(ts_code=symbol, start_date=ts_start, end_date=ts_end)
                elif asset_type == "hk_stock":
                    df = _self.pro.hk_daily(ts_code=symbol, start_date=ts_start, end_date=ts_end)
                df = _self._standardize_df(df, "tushare")

            # --- 2. Yahoo 路径 ---
            elif source == "yahoo" or (source == "tushare" and not _self.token):
                df = yf.download(symbol, start=yf_start, end=yf_end, progress=False)
                df = _self._standardize_df(df, "yahoo")

        except Exception as e:
            st.error(f"数据获取失败({source}): {e}")
            # --- 3. AkShare 最终兜底 (针对A股) ---
            if symbol.endswith((".SH", ".SZ")):
                try:
                    df = ak.stock_zh_a_hist(symbol=symbol[:6], start_date=ts_start, end_date=ts_end, adjust="qfq")
                    df = _self._standardize_df(df, "akshare")
                except:
                    return pd.DataFrame()
        
        return df