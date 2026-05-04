# ---------- IMPORTS ----------
import streamlit as st
import yfinance as yf
import pandas as pd


# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Stock Signal Dashboard", page_icon="💹", layout="wide")

st.markdown("""
<h1 style='text-align:center; color:#0A2A66;'>💹 Stock Signal Dashboard</h1>
<h4 style='text-align:center; color:#555;'>Daily Technical & Fundamental Insights for Your Watchlist</h4>
<hr>
""", unsafe_allow_html=True)


# ---------- SETTINGS ----------
SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]
SHORT_MA = 20
LONG_MA = 50


# ---------- RSI FUNCTION ----------
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ---------- MAIN SIGNAL GENERATOR ----------
def get_signals():
    results = []

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if df.empty or "Close" not in df.columns:
                continue

            # --- Technical calculations ---
            df["rsi"] = calc_rsi(df["Close"])
            df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
            df["ma_long"] = df["Close"].rolling(LONG_MA).mean()
            df["avg_vol"] = df["Volume"].rolling(10).mean()
            df.dropna(inplace=True)
            if df.empty:
                continue
            latest = df.iloc[-1]

            # --- Fundamental & sentiment data ---
            info = yf.Ticker(symbol).info
            recommend = info.get("recommendationMean")
            target_price = info.get("targetMeanPrice")
            pe_ratio = info.get("forwardPE")
            profit_margin = info.get("profitMargins")

            current_price = latest["Close"]
            upside = None
            if target_price:
                upside = round(((target_price - current_price) / current_price) * 100, 1)

            # --- Derived technical flags ---
            ma_cross = latest["ma_short"] > latest["ma_long"]
            low_rsi = latest["rsi"] < 50
            high_volume = latest["Volume"] > 1.5 * latest["avg_vol"]

            # --- Scoring system ---
            score = 0
            if ma_cross: score += 1
            if low_rsi: score += 1
            if high_volume: score += 1
            if recommend and recommend < 2.5: score += 1
            if upside and upside > 5: score += 1
            if pe_ratio and pe_ratio < 35: score += 1
            if profit_margin and profit_margin > 0.05: score += 1

            decision = "BUY" if score >= 4 else "WATCH"

            results.append({
                "Symbol": symbol,
                "Close Price": round(current_price, 2),
                "RSI": round(latest["rsi"], 1),
                "10‑Day Avg Vol": int(latest["avg_vol"]),
                "Today Vol": int(latest["Volume"]),
                "High Volume?": "✅" if high_volume else "",
                "Analyst Rating (1=Buy→5=Sell)": recommend,
                "Target Upside %": upside,
                "PE Ratio": pe_ratio,
                "Profit Margin": profit_margin,
                "Score": score,
                "Signal": decision
            })

        except Exception:
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
    st.subheader("No data available right now.")
else:
    st.subheader("📊 Combined Technical + Fundamental Signals")
    df_sorted = df.sort_values(by="Score", ascending=False)
    st.dataframe(df_sorted, use_container_width=True)

    buy_candidates = df_sorted[df_sorted["Signal"] == "BUY"]
    if not buy_candidates.empty:
        st.success(f"✅ {len(buy_candidates)} Potential BUY Opportunities Detected")
        st.table(
            buy_candidates[
                ["Symbol", "Close Price", "RSI", "Target Upside %", "Score", "Signal"]
            ]
        )
    else:
        st.info("No BUY signals met all criteria today.")

st.sidebar.header("⚙️ Settings")
st.sidebar.write("Reload after market close for updated indicators.")






