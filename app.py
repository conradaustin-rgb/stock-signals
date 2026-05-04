# ---------- IMPORTS ----------
import streamlit as st
import yfinance as yf
import pandas as pd


# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Stock Signal Dashboard", page_icon="💹", layout="wide")

st.markdown("""
<h1 style='text-align:center; color:#0A2A66;'>💹 Stock Signal Dashboard</h1>
<h4 style='text-align:center; color:#555;'>Daily Technical & Analyst Insights for Your Watchlist</h4>
<hr>
""", unsafe_allow_html=True)


# ---------- SETTINGS ----------
SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]
SHORT_MA = 20
LONG_MA = 50


# ---------- RSI CALCULATION ----------
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ---------- SIGNAL GENERATOR ----------
def get_signals():
    results = []

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if df.empty or "Close" not in df.columns:
                continue

            df["rsi"] = calc_rsi(df["Close"])
            df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
            df["ma_long"] = df["Close"].rolling(LONG_MA).mean()
            df = df.dropna()
            if df.empty:
                continue

            latest = df.iloc[-1]

            # Analyst data
            info = yf.Ticker(symbol).info
            recommend = info.get("recommendationMean")
            target_price = info.get("targetMeanPrice")
            current_price = latest["Close"]
            upside = None
            if recommend and target_price:
                upside = round(((target_price - current_price) / current_price) * 100, 1)

            # BUY condition
            if latest["ma_short"] > latest["ma_long"] and latest["rsi"] < 50:
                results.append({
                    "Symbol": symbol,
                    "Close Price": round(current_price, 2),
                    "RSI": round(latest["rsi"], 1),
                    "Analyst Rating (1=Buy→5=Sell)": recommend,
                    "Target Upside %": upside
                })
        except Exception:
            # Skip problem symbols quietly
            continue

    return pd.DataFrame(results)


# ---------- RUN APP ----------
try:
    df = get_signals()
except Exception as e:
    st.error(f"Problem generating signals: {e}")
    df = pd.DataFrame()

# ---------- DISPLAY ----------
if df.empty:
    st.subheader("No current BUY signals")
    st.caption("Technical criteria not met — showing latest RSI values for your watchlist.")
    rows = []
    for s in SYMBOLS:
        d = yf.download(s, period="6mo", interval="1d", progress=False)
        if d.empty:
            continue
        d["rsi"] = calc_rsi(d["Close"])
        last = d.iloc[-1]
        rows.append({"Symbol": s, "Price": round(last['Close'], 2), "RSI": round(last['rsi'], 1)})
    if rows:
        st.dataframe(pd.DataFrame(rows))
else:
    st.subheader("✅ Potential BUY Opportunities")
    st.dataframe(df)

st.sidebar.header("⚙️ Settings")
st.sidebar.write("Reload once a day after market close for the latest signals.")





