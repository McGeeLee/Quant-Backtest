import yfinance as yf
df = yf.download("AAPL", period="1d")
print(df)