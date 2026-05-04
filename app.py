# -----------------  IMPORTS  -----------------
import streamlit as st
import yfinance as yf
import pandas as pd

# -----------------  PAGE SETUP  -----------------
st.set_page_config(
    page_title="Stock Signal Dashboard",
    page_icon="💹",
    layout="wide"
)

# -----------------  STYLING  -----------------
st.markdown("""
    <style>
        body {
            background-color: #f9fafc;
            color: #0a1a33;
            font-family: 'Inter', sans-serif;
        }
        .main {
            padding: 2rem 3rem;
        }
        h1 {
            text-align: center;
            color: #0A2A66;
            font-size: 42px;
            margin-bottom: 0;
        }
        h4 {
            text-align: center;
            color: #4b5563;
            margin-top: 4px;
        }
        hr {
            border: 1px solid #0A2A66;
            margin: 1.5rem 0;
        }
        .stAlert {
            font-size: 15px !important;
            border-radius: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

# -----------------  HEADER  -----------------
st.markdown("""
<h1>💹 Stock Signal Dashboard</h1>
<h4>Daily Technical & Analyst Insights for Your Watchlist</h4>
<hr/>
""", unsafe_allow_html=True)

# -----------------  PARAMETERS  -----------------
SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]
SHORT_MA = 20
LONG_MA = 50

# -----------------  RSI FUNCTION  -----------------
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# -----------------  MAIN SIGNAL FUNCTION  -----------------
def get_signals():
    results = []

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if df.empty or "Close" not in df.columns:
                st.warning(f"Skipped {symbol} due to data issue.")
                continue

            df = df.dropna(subset=["Close"])
            df["rsi"] = calc_rsi(df["Close"])
            df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
            df["ma_long"] = df["Close"].rolling(LONG_MA).mean()
            df = df.dropna()
            if df.empty:
                continue
            latest = df.iloc[-1]

            ticker = yf.Ticker(symbol)
            info = ticker.info
            recommend = info.get("recommendationMean", None)
            target_price = info.get("targetMeanPrice", None)
            current_price = latest["Close"]
            if recommend and target_price:
                upside = round(((target_price - current_price) / current_price) * 100, 1)
            else:
                recommend, upside = None, None

            if (
                latest["ma_short"] > latest["ma_long"]
                and latest["rsi"] < 50
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

# -----------------  RUN APP  -----------------
try:
    df = get_signals()
except Exception as e:
    st.error(f"Problem generating signals: {e}")
    df = None

if df is None or df.empty:
    st.markdown("### ❗ No qualifying BUY signals today")
    st.caption("Technical criteria not met — showing raw RSI data for transparency.")

    placeholder_rows = []
    for symbol in SYMBOLS:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if data.empty:
            continue
        data["rsi"] = calc_rsi(data["Close"])
        last = data.iloc[-1]
        placeholder_rows.append({
            "Symbol": symbol,
            "Price": round(last["Close"], 2),
            "RSI": round(last["rsi"], 1)
        })

    if placeholder_rows:
        styled = (
            pd.DataFrame(placeholder_rows)
            .style.background_gradient(subset=["RSI"], cmap="RdYlGn_r")
            .format({"Price": "${:,.2f}", "RSI": "{:.1f}"})
        )
        st.dataframe(styled, use_container_width=True)
else:
    st.markdown("### ✅ Potential BUY Opportunities")
    styled = (
        df.style.background_gradient(
            subset=["RSI", "Target Upside %"], cmap="RdYlGn_r"
        )
        .format({
            "Close Price": "${:,.2f}",
            "RSI": "{:.1f}",
            "Target Upside %": "{:.1f}",
        })
    )
    st.dataframe(styled, use_container_width=True)

st.sidebar.markdown("### ⚙️ Settings")
st.sidebar.caption("Reload this page once a day after market close for the latest signals.")




