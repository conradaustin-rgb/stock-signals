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
    rows = []

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, period="1y", interval="1d", progress=False)
            if df.empty or "Close" not in df.columns:
                continue

            # --- Technical indicators ---
            df["rsi"] = calc_rsi(df["Close"])
            df["ma_short"] = df["Close"].rolling(SHORT_MA).mean()
            df["ma_long"] = df["Close"].rolling(LONG_MA).mean()
            df["avg_vol"] = df["Volume"].rolling(10).mean()
            df.dropna(inplace=True)
            if df.empty:
                continue
            last = df.iloc[-1]

            # --- Analyst & fundamentals ---
            info = yf.Ticker(symbol).info
            recommend = info.get("recommendationMean") or None
            target_price = info.get("targetMeanPrice") or None
            pe_ratio = info.get("forwardPE") or None
            profit_margin = info.get("profitMargins") or None

            price = last["Close"]
            upside = None
            if target_price:
                upside = round(((target_price - price) / price) * 100, 1)

            # --- Technical flags ---
            ma_cross = last["ma_short"] > last["ma_long"]
            low_rsi = last["rsi"] < 55
            high_volume = last["Volume"] > 1.5 * last["avg_vol"]

            # --- Scoring (0–7) ---
            score = 0
            if ma_cross: score += 1
            if low_rsi: score += 1
            if high_volume: score += 1
            if recommend and recommend < 2.5: score += 1
            if upside and upside > 5: score += 1
            if pe_ratio and pe_ratio < 35: score += 1
            if profit_margin and profit_margin > 0.05: score += 1

            decision = "BUY" if score >= 3 else "WATCH"

            rows.append({
                "Symbol": symbol,
                "Close Price": round(price, 2),
                "RSI": round(last["rsi"], 1),
                "10‑Day Avg Vol": int(last["avg_vol"]),
                "Today Vol": int(last["Volume"]),
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

    return pd.DataFrame(rows)


# ---------- RUN APP ----------
df = pd.DataFrame()
try:
    df = get_signals()
except Exception as e:
    st.error(f"Couldn't load data: {e}")

# ---------- DISPLAY ----------
if df.empty:
    st.warning("No data available right now — showing basic RSI for reference.")
    backup = []
    for s in SYMBOLS:
        data = yf.download(s, period="6mo", interval="1d", progress=False)
        if data.empty:
            continue
        data["rsi"] = calc_rsi(data["Close"])
        latest = data.iloc[-1]
        backup.append({"Symbol": s, "Price": round(latest["Close"], 2), "RSI": round(latest["rsi"], 1)})
    if backup:
        st.dataframe(pd.DataFrame(backup), use_container_width=True)
else:
    st.subheader("📊 Combined Indicators & Scores")
    df_sorted = df.sort_values(by="Score", ascending=False)
    st.dataframe(df_sorted, use_container_width=True)

    buy_df = df_sorted[df_sorted["Signal"] == "BUY"]
    if not buy_df.empty:
        st.success(f"✅ {len(buy_df)} Potential BUY Opportunities Detected")
        st.table(
            buy_df[
                ["Symbol", "Close Price", "RSI", "Target Upside %", "Score", "Signal"]
            ].reset_index(drop=True)
        )
    else:
        st.info("No active BUY signals — revisit after the next trading session.")

st.sidebar.header("⚙️ Settings")
st.sidebar.write("Reload after market close (approx 9 PM UTC) for updated data.")







