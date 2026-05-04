import yfinance as yf
import pandas as pd
import streamlit as st
import ta

st.title("📈 Simple Stock Buy Signals")

SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
SHORT_MA = 20
LONG_MA = 50

def get_signals():
    results = []
    for symbol in SYMBOLS:
        df = yf.download(symbol, period="90d")
        df["rsi"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
        df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
        df["ma_long"] = df["Close"].rolling(LONG_MA).mean()
        latest = df.iloc[-1]
        if (
            latest["ma_short"] > latest["ma_long"]
            and latest["rsi"] < 40
            and latest["Close"] > latest["ma_short"]
        ):
            results.append({
                "Symbol": symbol,
                "Close": round(latest["Close"], 2),
                "RSI": round(latest["rsi"], 1),
            })
    return pd.DataFrame(results)

df = get_signals()
if df.empty:
    st.info("No strong buy signals today.")
else:
    st.success("Possible Buy Signals:")
    st.dataframe(df)
