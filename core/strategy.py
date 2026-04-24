class StrategyLibrary:
    @staticmethod
    def perfect_prediction(df, fee):
        """增强版完美预测：考虑了 High/Low 的波动"""
        df = df.copy()
        # 这里的逻辑可以升级：只有当 (high - open) 超过手续费才买入
        df['change'] = (df['close'] - df['open']) / df['open']
        df['signal'] = np.where(df['change'].abs() > (fee * 2), np.sign(df['change']), 0)
        
        # 计算策略净值
        df['strategy_ret'] = df['signal'] * df['change'] - (df['signal'].diff().abs() * fee)
        df['equity'] = (1 + df['strategy_ret']).cumprod()
        return df