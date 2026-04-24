import yfinance as yf
import tushare as ts
import pandas as pd
import numpy as np

class DataFetcher:
    def __init__(self, token=None):
        self.token = token
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()

    def fetch(self, symbol, start, end):
        """
        统一入口：自动识别 A股 (.SH/.SZ) 或全球资产
        """
        # 统一日期格式：确保是 YYYY-MM-DD 格式供 Yahoo 使用
        start_yf = start.replace('', '') # 假设输入是 20240101 或 2024-01-01
        if len(start) == 8 and '-' not in start:
            start_yf = f"{start[:4]}-{start[4:6]}-{start[6:]}"
            end_yf = f"{end[:4]}-{end[4:6]}-{end[6:]}"
        else:
            start_yf, end_yf = start, end

        if ".SH" in symbol.upper() or ".SZ" in symbol.upper():
            return self._fetch_tushare(symbol.upper(), start.replace('-', ''), end.replace('-', ''))
        else:
            return self._fetch_yahoo(symbol, start_yf, end_yf)

    def _fetch_yahoo(self, symbol, start, end):
        try:
            df = yf.download(symbol, start=start, end=end, progress=False)
            if df.empty:
                return pd.DataFrame()
            
            # 处理 yfinance 的 MultiIndex 列名问题
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            
            # 映射字段：确保包含 datetime, open, high, low, close, volume
            df = df.rename(columns={'date': 'datetime', 'adj close': 'close'})
            
            # 强制转换数值类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            return df[['datetime', 'open', 'high', 'low', 'close', 'volume']].dropna()
        except Exception as e:
            print(f"Yahoo数据获取失败: {e}")
            return pd.DataFrame()

    def _fetch_tushare(self, symbol, start, end):
        if not self.token:
            raise ValueError("获取 A 股数据需要 Tushare Token")
        
        try:
            # 识别是股票还是基金(ETF)
            if symbol.startswith(('51', '58', '15')):
                df = self.pro.fund_daily(ts_code=symbol, start_date=start, end_date=end)
            else:
                df = self.pro.daily(ts_code=symbol, start_date=start, end_date=end)
            
            if df.empty:
                return pd.DataFrame()

            # 统一字段名为小写并映射
            df = df.rename(columns={
                'trade_date': 'datetime',
                'vol': 'volume'
            })
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')
            
            # 字段对齐
            cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            return df[cols].reset_index(drop=True)
        except Exception as e:
            print(f"Tushare数据获取失败: {e}")
            return pd.DataFrame()