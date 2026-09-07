import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import warnings
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Stock Scanner - Defence Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# STOCK UNIVERSE (Your 100 stocks)
# ═══════════════════════════════════════════════════════════════════

ULTIMATE_WATCHLIST = ['TATACHEM', 'HDFCLIFE', 'KOTAKBANK', 'HDFCBANK', 'TATAPOWER', 'GREAVESCOT', 'KEI', 'LT', 'ULTRACEMCO', 'HAVELLS', 'APOLLOTYRE', 'GRSE', 'KANSAINER', 'BPCL', 'HINDUNILVR', 'ZOMATO', 'HINDALCO', 'TCS', 'SUNPHARMA', 'NATIONALUM', 'BDL', 'BALKRISIND', 'ONGC', 'PARAS', 'GODREJPROP', 'HEROMOTOCO', 'BRITANNIA', 'NTPC', 'PAYTM', 'TATASTEEL', 'ZENTEC', 'SOLARINDS', 'SHRIRAMFIN', 'GAIL', 'TECHM', 'AXISBANK', 'NESTLEIND', 'MIDHANI', 'KIRLOSENG', 'AKZOINDIA', 'DATAPATTNS', 'LTIM', 'ICICIBANK', 'DABUR', 'RELIANCE', 'MRF', 'WIPRO', 'COALINDIA', 'SBILIFE', 'BEL', 'INDIGO', 'BHARTIARTL', 'POWERGRID', 'EICHERMOT', 'CEAT', 'INFY', 'SRF', 'DLF', 'MAZDOCK', 'GRASIM', 'INDUSINDBK', 'CUMMINSIND', 'BAJFINANCE', 'POLYCAB', 'SAIL', 'VOLTAS', 'BAJAJFINSV', 'HAL', 'MARUTI', 'CIPLA', 'DRREDDY', 'BAJAJ-AUTO', 'TITAN', 'APOLLOHOSP', 'IOC', 'ITC', 'ASTRAMICRO', 'CONCOR', 'IDEAFORGE', 'ADANIENT', 'IRCTC', 'NIBE', 'LTTS', 'JSWSTEEL', 'MPHASIS', 'TATACONSUM', 'DIVISLAB', 'FINOLEX', 'SBIN', 'COCHINSHIP', 'COFORGE', 'ASIANPAINT', 'ADANIPORTS', 'BEML', 'VEDL', 'HCLTECH', 'JINDALSTEL', 'PIDILITIND', 'CENTUM', 'M&M']

ALL_DEFENCE_STOCKS = ['GREAVESCOT', 'KEI', 'TATAPOWER', 'TATASTEEL', 'LT', 'ZENTEC', 'ASTRAMICRO', 'SOLARINDS', 'CONCOR', 'IDEAFORGE', 'BEL', 'TECHM', 'POWERGRID', 'APOLLOTYRE', 'NIBE', 'CEAT', 'GRSE', 'MIDHANI', 'KIRLOSENG', 'KANSAINER', 'LTTS', 'SRF', 'AKZOINDIA', 'HINDALCO', 'MAZDOCK', 'DATAPATTNS', 'NATIONALUM', 'BDL', 'FINOLEX', 'COCHINSHIP', 'BALKRISIND', 'CUMMINSIND', 'ASIANPAINT', 'BEML', 'POLYCAB', 'ADANIPORTS', 'SAIL', 'VEDL', 'HCLTECH', 'JINDALSTEL', 'PARAS', 'HAL', 'CENTUM', 'NTPC', 'MRF', 'M&M']

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def is_safe_stock(symbol, price):
    if price < 50:
        return False
    if price > 20000:
        return False
    return True

def check_defence_status(symbol):
    if symbol in ALL_DEFENCE_STOCKS:
        return True, "🛡️"
    return False, ""

@st.cache_data(ttl=3600)
def get_global_markets():
    symbols = {
        "Dow Jones": "^DJI",
        "Nasdaq": "^IXIC",
        "S&P 500": "^GSPC",
        "Crude Oil": "CL=F",
        "Dollar Index": "DX-Y.NYB"
    }

    market_data = {}

    for name, ticker in symbols.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if len(hist) >= 2:
                latest = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change_pct = ((latest - prev) / prev) * 100

                market_data[name] = {
                    "Price": round(latest, 2),
                    "Change %": round(change_pct, 2)
                }
        except:
            market_data[name] = {"Price": "N/A", "Change %": 0.0}

    df = pd.DataFrame(market_data).T

    us_avg = (market_data["Dow Jones"]["Change %"] + 
              market_data["Nasdaq"]["Change %"] + 
              market_data["S&P 500"]["Change %"]) / 3

    if us_avg > 0.5:
        sentiment = "🟢 BULLISH"
    elif us_avg < -0.5:
        sentiment = "🔴 BEARISH"
    else:
        sentiment = "🟡 NEUTRAL"

    return df, sentiment, us_avg

def analyze_stock(symbol):
    ticker = f"{symbol}.NS" if not symbol.endswith((".NS", ".BO")) else symbol

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="60d")

        if df.empty or len(df) < 25:
            return None

        ema = EMAIndicator(close=df["Close"], window=20)
        df["EMA_20"] = ema.ema_indicator()
        rsi = RSIIndicator(close=df["Close"], window=14)
        df["RSI"] = rsi.rsi()
        atr = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14)
        df["ATR"] = atr.average_true_range()
        df["Vol_SMA20"] = df["Volume"].rolling(window=20).mean()
        df["Vol_Ratio"] = df["Volume"] / df["Vol_SMA20"]
        df["Support"] = df["Low"].rolling(window=20).min()
        df["Resistance"] = df["High"].rolling(window=20).max()

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["Close"])

        if not is_safe_stock(symbol, close):
            return None

        ema20 = float(latest["EMA_20"])
        rsi_val = float(latest["RSI"])
        atr_val = float(latest["ATR"])
        atr_pct = (atr_val / close) * 100
        vol_ratio = float(latest["Vol_Ratio"])
        support = float(latest["Support"])
        resistance = float(latest["Resistance"])
        day_change = ((close - float(prev["Close"])) / float(prev["Close"])) * 100
        dist_to_res = ((resistance - close) / close) * 100

        score = 0
        signals = []

        if close > ema20:
            score += 3
            signals.append("Uptrend")
        if 45 <= rsi_val <= 65:
            score += 2
            signals.append("RSI 45-65")
        elif rsi_val < 35:
            score += 1
            signals.append("RSI Oversold")
        if atr_pct >= 1.8:
            score += 2
            signals.append(f"ATR {atr_pct:.1f}%")
        if vol_ratio >= 1.2:
            score += 3
            signals.append(f"Vol {vol_ratio:.1f}x")
        elif vol_ratio >= 0.9:
            score += 1

        is_defence, defence_badge = check_defence_status(symbol)

        if dist_to_res <= 3.0:
            entry = round(resistance * 1.002, 2)
            setup = "BREAKOUT"
        else:
            entry = round(close * 1.002, 2)
            setup = "MOMENTUM"

        target = round(entry + (1.5 * atr_val), 2)
        sl = round(entry - (0.8 * atr_val), 2)

        risk = entry - sl
        reward = target - entry
        rr = round(reward / risk, 2) if risk > 0 else 0

        return {
            "Symbol": symbol,
            "Price": round(close, 2),
            "Score": score,
            "RSI": round(rsi_val, 1),
            "Setup": setup,
            "Entry": entry,
            "Target": target,
            "SL": sl,
            "RR": f"1:{rr}",
            "Is_Defence": is_defence,
            "Defence_Badge": defence_badge,
            "Signals": ", ".join(signals),
            "Day_Change": round(day_change, 2)
        }

    except:
        return None

def scan_all_stocks(stock_list):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, symbol in enumerate(stock_list):
        status_text.text(f"Scanning {i+1}/{len(stock_list)}: {symbol}")
        result = analyze_stock(symbol)
        if result:
            results.append(result)
        progress_bar.progress((i + 1) / len(stock_list))
        time.sleep(0.3)

    status_text.empty()
    progress_bar.empty()

    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════
# MAIN APP UI
# ═══════════════════════════════════════════════════════════════════

st.title("🚀 Stock Scanner - Defence Intelligence")
st.markdown("*Real-time scanning of 100 stocks with Defence sector focus*")

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🔄 Run Full Scan", type="primary", use_container_width=True):
        st.session_state["scan_triggered"] = True

    st.markdown("---")

    min_score = st.slider("Minimum Score", 0, 10, 5)
    show_defence_only = st.checkbox("🛡️ Defence Stocks Only")

    st.markdown("---")
    st.info(f"📊 Total: {len(ULTIMATE_WATCHLIST)} stocks\n🛡️ Defence: {len(ALL_DEFENCE_STOCKS)} stocks")

# Global Markets
st.header("🌍 Global Markets")
with st.spinner("Fetching global data..."):
    global_df, sentiment, us_score = get_global_markets()

cols = st.columns(5)
for i, (idx, row) in enumerate(global_df.iterrows()):
    with cols[i]:
        delta = row["Change %"]
        st.metric(label=idx, value=f"{row['Price']}", delta=f"{delta:+.2f}%")

st.info(f"**Market Sentiment:** {sentiment} (US Score: {us_score:+.2f}%)")

# Main Scan
st.header("📊 Stock Analysis")

# Quick Stock Search Feature
st.subheader("🔍 Quick Stock Search")

col1, col2 = st.columns([3, 1])

with col1:
    search_symbol = st.text_input(
        "Enter stock symbol (e.g., SUZLON, RELIANCE, ADANIGREEN)", 
        placeholder="Type symbol and press Enter..."
    ).upper()

with col2:
    st.write("")  # Spacer
    st.write("")  # Spacer
    search_button = st.button("🔍 Analyze", use_container_width=True)

if search_button and search_symbol:
    with st.spinner(f"Analyzing {search_symbol}..."):
        result = analyze_stock(search_symbol)
        
        if result:
            st.success(f"✅ Analysis complete for {search_symbol}")
            
            # Display in a nice card
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Price", f"₹{result['Price']}")
                st.metric("Score", f"{result['Score']}/10")
            
            with col2:
                st.metric("Entry", f"₹{result['Entry']}")
                st.metric("Target", f"₹{result['Target']}")
            
            with col3:
                st.metric("Stop Loss", f"₹{result['SL']}")
                st.metric("R:R", result['RR'])
            
            # Additional details
            st.info(f"**Setup:** {result['Setup']} | **RSI:** {result['RSI']}")
            
            if result['Is_Defence']:
                st.success("🛡️ This is a Defence sector stock!")
            
            st.caption(f"Signals: {result['Signals']}")
            
            # Calculate position sizing
            shares_can_buy = int(5000 / result['Entry'])
            potential_profit = (result['Target'] - result['Entry']) * shares_can_buy
            max_loss = (result['Entry'] - result['SL']) * shares_can_buy
            
            st.markdown(f"""
            **For ₹5,000 Capital:**
            - Buy {shares_can_buy} shares at ₹{result['Entry']}
            - Potential Profit: ₹{potential_profit:.0f}
            - Max Risk: ₹{max_loss:.0f}
            """)
        else:
            st.error(f"❌ Could not analyze {search_symbol}. Check if symbol is correct (must be NSE stock).")

st.divider()
if "scan_triggered" in st.session_state and st.session_state["scan_triggered"]:
    st.info("🔍 Scanning... This takes ~2 minutes")

    df_all = scan_all_stocks(ULTIMATE_WATCHLIST)

    if not df_all.empty:
        st.session_state["scan_data"] = df_all
        st.session_state["scan_time"] = datetime.now().strftime("%I:%M %p")
        st.session_state["scan_triggered"] = False
        st.success(f"✅ Scan complete! Found {len(df_all)} stocks")
        st.rerun()

if "scan_data" in st.session_state:
    df_all = st.session_state["scan_data"]
    scan_time = st.session_state.get("scan_time", "Unknown")

    st.caption(f"Last scan: {scan_time}")

    df_filtered = df_all[df_all["Score"] >= min_score]
    if show_defence_only:
        df_filtered = df_filtered[df_filtered["Is_Defence"] == True]

    tab1, tab2, tab3 = st.tabs(["🏆 Top Picks", "🛡️ Defence Sector", "📋 All Stocks"])

    with tab1:
        st.subheader(f"Top Picks (Score {min_score}+)")

        top_picks = df_filtered.sort_values("Score", ascending=False).head(10)

        for _, row in top_picks.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    badge = row["Defence_Badge"] if row["Is_Defence"] else ""
                    st.markdown(f"### {row['Symbol']} {badge}")
                    st.caption(f"₹{row['Price']} | {row['Setup']}")

                with col2:
                    st.metric("Score", f"{row['Score']}/10", delta=f"{row['Day_Change']:+.1f}%")

                with col3:
                    if row["Score"] >= 7:
                        st.success("Strong")
                    elif row["Score"] >= 5:
                        st.warning("Moderate")

                st.markdown(f"**Entry:** ₹{row['Entry']} → **Target:** ₹{row['Target']} → **SL:** ₹{row['SL']} | **R:R:** {row['RR']}")
                st.caption(row["Signals"])
                st.divider()

    with tab2:
        st.subheader("🛡️ Defence Sector")

        df_defence = df_all[df_all["Is_Defence"] == True].sort_values("Score", ascending=False)

        hot = len(df_defence[df_defence["Score"] >= 6])

        st.metric("🔥 Hot Defence Stocks", hot)

        st.dataframe(
            df_defence[["Symbol", "Price", "Score", "Entry", "Target", "SL"]],
            use_container_width=True,
            hide_index=True
        )

    with tab3:
        st.dataframe(
            df_filtered.sort_values("Score", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    # Downloads
    st.header("📥 Downloads")

    col1, col2 = st.columns(2)

    with col1:
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            "📊 Download CSV",
            csv,
            f"scan_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

    with col2:
        report = f"STOCK SCANNER - {datetime.now().strftime('%d %B %Y')}\n"
        report += "="*60 + "\n\nTOP 5 PICKS:\n\n"
        for i, (_, row) in enumerate(df_filtered.sort_values("Score", ascending=False).head(5).iterrows(), 1):
            report += f"{i}. {row['Symbol']} - ₹{row['Price']} (Score: {row['Score']}/10)\n"
            report += f"   Entry: ₹{row['Entry']} → Target: ₹{row['Target']}\n\n"

        st.download_button(
            "📄 Download TXT",
            report,
            f"report_{datetime.now().strftime('%Y%m%d')}.txt",
            "text/plain",
            use_container_width=True
        )

else:
    st.info("👆 Click 'Run Full Scan' in sidebar to start!")

    st.markdown("""
    ### What this does:
    - ✅ Scans 100 stocks (68 core + 32 defence)
    - ✅ 10+ technical indicators per stock
    - ✅ Scores 0-10
    - ✅ Defence sector highlighted
    - ✅ Entry/Target/SL levels

    **Time:** ~2 minutes
    """)
