import yfinance as yf
import pandas as pd
import streamlit as st
import ta
st_autorefresh = st.experimental_rerun if False else None
st.set_page_config(page_title="Stock Buy Signals", page_icon="📈", layout="centered")
st.title("📈 Simple Stock Buy Signals")

SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA",
    "META", "NFLX", "BABA", "AMD", "INTC"
]

SHORT_MA = 20
LONG_MA = 50

def get_signals():
    results = []

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if df.empty or "Close" not in df.columns:
                continue

            # Clean data and drop missing values
            df = df.dropna(subset=["Close"])
            df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
            df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
            df["ma_long"] = df["Close"].rolling(LONG_MA).mean()

            df = df.dropna()  # remove initial NaNs
            if df.empty:
                continue

            latest = df.iloc[-1]

            if (
                latest["ma_short"] > latest["ma_long"]
                and latest["rsi"] < 40
                and latest["Close"] > latest["ma_short"]
            ):
                results.append({
                    "Symbol": symbol,
                    "Close Price": round(latest["Close"], 2),
                    "RSI": round(latest["rsi"], 1),
                    "Short MA": round(latest["ma_short"], 2),
                    "Long MA": round(latest["ma_long"], 2)
                })
        except Exception as e:
            st.warning(f"Skipped {symbol} due to data issue: {e}")

    return pd.DataFrame(results)

def get_signals():
    results = []

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if df.empty or "Close" not in df.columns:
                continue

            # ---- Technical indicators ----
            df = df.dropna(subset=["Close"])
            df["rsi"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
            df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
            df["ma_long"] = df["Close"].rolling(LONG_MA).mean()
            df = df.dropna()
            if df.empty:
                continue
            latest = df.iloc[-1]

            # ---- Analyst data from Yahoo ----
            ticker = yf.Ticker(symbol)
            info = ticker.info
            recommend = info.get("recommendationMean", None)
            target_price = info.get("targetMeanPrice", None)
            current_price = latest["Close"]
            if recommend and target_price:
                upside = round(((target_price - current_price) / current_price) * 100, 1)
            else:
                recommend, upside = None, None

            # ---- Combine technical + analyst filters ----
            if (
                latest["ma_short"] > latest["ma_long"]
                and latest["rsi"] < 40
                and latest["Close"] > latest["ma_short"]
            ):
                results.append({
                    "Symbol": symbol,
                    "Close Price": round(latest["Close"], 2),
                    "RSI": round(latest["rsi"], 1),
                    "Analyst Rating (1=Buy→5=Sell)": recommend,
                    "Target Upside %": upside
                })

        except Exception as e:
            st.warning(f"Skipped {symbol}: {e}")

    return pd.DataFrame(results)


# --- End of app ---
st.sidebar.info("🔁 Tip: reload this page each day to get fresh data.")



