import pandas as pd
import tushare as ts
import yfinance as yf
import akshare as ak
import streamlit as st
from datetime import datetime

class UniversalDataHub:
    def __init__(self, tushare_token="765e94535372b39b7790739a2ba7400db7c4e35a93b333dbd6b5a231"):
        self.token = tushare_token
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()

    def detect_asset_and_source(self, symbol: str):
        symbol = symbol.upper()
        if "-USD" in symbol: return "crypto", "akshare"
        if symbol.endswith((".SH", ".SZ")): return "a_stock", "tushare"
        if symbol.endswith(".HK"): return "hk_stock", "tushare"
        return "us_stock", "akshare"

    def _format_date(self, date_obj, target_format="%Y%m%d"):
        if isinstance(date_obj, str):
            clean = date_obj.replace("-", "").replace("/", "")
            if target_format == "%Y-%m-%d" and len(clean) == 8:
                return f"{clean[:4]}-{clean[4:6]}-{clean[6:]}"
            return clean
        return date_obj.strftime(target_format)

    def _standardize_df(self, df, source):
        if df is None or df.empty: return pd.DataFrame()
        
        # 统一映射表
        maps = {
            "tushare": {'trade_date': 'datetime', 'vol': 'volume', 'amount': 'amount'},
            "akshare": {'日期': 'datetime', '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume', '成交额': 'amount', '成交量(手)': 'volume'}
        }
        
        df = df.rename(columns=maps.get(source, {}))
        
        # 索引标准化
        if 'datetime' not in df.columns:
            df = df.reset_index().rename(columns={'Date': 'datetime', 'index': 'datetime'})
        
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df.columns = [c.lower() for c in df.columns]

        # 补全 6 大金刚字段
        standard_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in standard_cols:
            if col not in df.columns:
                df[col] = df['close'] * df['volume'] if col == 'amount' else 0.0
                
        return df[standard_cols].sort_index()

    @st.cache_data(ttl=3600)
    def get_data(_self, symbol: str, start: str, end: str):
        asset_type, source = _self.detect_asset_and_source(symbol)
        s_dt = _self._format_date(start, "%Y%m%d")
        e_dt = _self._format_date(end, "%Y%m%d")
        
        df = pd.DataFrame()

        try:
            # --- 1. Tushare 核心逻辑 (A股/港股) ---
            if source == "tushare":
                if asset_type == "a_stock":
                    df = _self.pro.daily(ts_code=symbol, start_date=s_dt, end_date=e_dt)
                elif asset_type == "hk_stock":
                    df = _self.pro.hk_daily(ts_code=symbol, start_date=s_dt, end_date=e_dt)
                return _self._standardize_df(df, "tushare")

            # --- 2. AkShare 动态降级逻辑 (美股/币) ---
            else:
                if asset_type == "us_stock":
                    # 尝试从东方财富源获取美股历史
                    df = ak.stock_us_hist(symbol=symbol, period="daily", start_date=s_dt, end_date=e_dt, adjust="qfq")
                elif asset_type == "crypto":
                    # 尝试主流币安行情源
                    coin = symbol.replace("-USD", "").lower() + "usdt"
                    df = ak.crypto_hist_binance(symbol=coin, period="daily", start_date=s_dt, end_date=e_dt)
                
                if df.empty: # 如果 Ak 失败，最后一次尝试 Yahoo (如果你开了全局代理)
                    yf_s, yf_e = _self._format_date(start, "%Y-%m-%d"), _self._format_date(end, "%Y-%m-%d")
                    df = yf.download(symbol, start=yf_s, end=yf_e, progress=False)
                    return _self._standardize_df(df, "yahoo")
                
                return _self._standardize_df(df, "akshare")

        except Exception as e:
            st.error(f"❌ {symbol} 彻底获取失败: {e}")
            return pd.DataFrame()