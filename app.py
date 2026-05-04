st.set_page_config(page_title="Stock Signal Dashboard", page_icon="💹", layout="wide")
st.markdown(
    """
    <h1 style='text-align: center; color: #0A2A66; font-size: 40px;'>
        💹 Stock Signal Dashboard
    </h1>
    <h4 style='text-align: center; color: #555555;'>
        Daily Technical & Analyst Insights for Your Watchlist
    </h4>
    <hr style='border: 1px solid #0A2A66;'/>
    """,
    unsafe_allow_html=True
)

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

df = get_signals()

if df.empty:
    st.warning("No stocks met the full BUY criteria, showing RSI values for all instead:")

    rows = []
    for symbol in SYMBOLS:
        df_temp = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df_temp.empty:
            continue
# ---- Function to calculate RSI (avoids ta library errors) ----
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ---- Display results ----
df = get_signals()

if df.empty:
    st.warning("No stocks met the full BUY criteria, showing RSI values for all instead:")

    rows = []
    for symbol in SYMBOLS:
        df_temp = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df_temp.empty:
            continue
        df_temp["rsi"] = calc_rsi(df_temp["Close"])
        last = df_temp.iloc[-1]
        rows.append({
            "Symbol": symbol,
            "Price": round(last["Close"], 2),
            "RSI": round(last["rsi"], 1)
        })

    if rows:
        st.dataframe(pd.DataFrame(rows))
else:
    st.success("✅ Possible Buy Signals:")
    st.dataframe(df)

st.sidebar.info("🔁 Tip: reload this page each day to get fresh data.")



# --- End of app ---
st.sidebar.info("🔁 Tip: reload this page each day to get fresh data.")



