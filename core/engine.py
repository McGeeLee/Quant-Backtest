import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_cash=100000.0, commission=0.0001):
        self.cash = initial_cash
        self.commission = commission
        self.portfolio_value = []
        self.dates = []
        
    def calculate_performance(self, equity_series):
        """计算专业回测指标"""
        returns = equity_series.pct_change().dropna()
        
        # 1. 累计收益
        total_return = (equity_series.iloc[-1] / equity_series.iloc[0]) - 1
        
        # 2. 最大回撤 (Max Drawdown)
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 3. 夏普比率 (假设无风险利率 2%)
        sharpe = (returns.mean() * 252 - 0.02) / (returns.std() * np.sqrt(252)) if len(returns) > 0 else 0
        
        return {
            "Total Return": total_return,
            "Max Drawdown": max_drawdown,
            "Sharpe Ratio": sharpe,
            "Equity Curve": equity_series
        }