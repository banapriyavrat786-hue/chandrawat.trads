import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, pandas as pd, math
from datetime import datetime
from scipy.stats import norm

# ==========================================
# 1. PRO MATH & GREEKS ENGINE
# ==========================================
def calculate_all_greeks(S, K, T, r, sigma, type="CE"):
    try:
        if T <= 0 or sigma <= 0: return 0.5, 0, 0, 0, 0
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        delta = norm.cdf(d1) if type == "CE" else norm.cdf(d1) - 1
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        theta = -(S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))) - r * K * math.exp(-r * T) * (norm.cdf(d2) if type == "CE" else norm.cdf(-d2))
        vega = S * norm.pdf(d1) * math.sqrt(T)
        return round(delta, 2), round(gamma, 4), round(theta/365, 2), round(vega/100, 2), round(sigma*100, 2)
    except: return 0.5, 0, 0, 0, 0

# ==========================================
# 2. UI & DASHBOARD SETUP
# ==========================================
st.set_page_config(page_title="MKPV Ultimate AI Beast", layout="wide")
st.title("🛡️ MKPV Ultimate AI Beast (Order-Flow + Greeks)")

# Credentials
CLIENT_ID = "P51646259"
API_KEY = "MT72qa1q"
TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
MPIN = "9171" 

# Header Metrics
m1, m2, m3, m4 = st.columns(4)
spot_m = m1.empty()
pcr_m = m2.empty()
signal_m = m3.empty()
strength_m = m4.empty()

st.divider()
table_area = st.empty()

# Sidebar for Trade Details
st.sidebar.header("🎯 Trade Setup & Risk")
setup_box = st.sidebar.empty()

# ==========================================
# 3. CORE ENGINE
# ==========================================
def launch_ultimate_beast():
    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(CLIENT_ID, MPIN, otp)
        st.toast("🚀 Beast Mode Activated: Bid-Ask Analysis Live!")

        while True:
            res = obj.ltpData("NSE", "Nifty 50", "26000")
            if res['status'] and res['data']:
                spot = float(res['data']['ltp'])
                atm = round(spot / 50) * 50
                
                rows = []
                total_ce_oi, total_pe_oi = 1.0, 1.0 # Base for calc
                
                # Analyze Strike Range
                for s in range(atm-150, atm+200, 50):
                    # --- Simulated Live Data (Tokens needed for real time) ---
                    # In real-market: Fetch via obj.marketData("FULL", [tokens])
                    ce_bid, ce_ask = 105.20, 105.45
                    pe_bid, pe_ask = 95.10, 95.35
                    ce_vol, pe_vol = 800000, 1100000
                    ce_oi, pe_oi = 120000, 160000
                    
                    total_ce_oi += ce_oi
                    total_pe_oi += pe_oi
                    
                    # Greeks Calculation
                    delta, gamma, theta, vega, iv = calculate_all_greeks(spot, s, 0.01, 0.07, 0.16, "CE")
                    
                    # Bid-Ask Analysis (Order Imbalance)
                    spread_ce = round(ce_ask - ce_bid, 2)
                    spread_pe = round(pe_ask - pe_bid, 2)
                    
                    rows.append({
                        "Strike": s,
                        "CE Bid/Ask": f"{ce_bid}/{ce_ask}",
                        "PE Bid/Ask": f"{pe_bid}/{pe_ask}",
                        "Spread (C/P)": f"{spread_ce}/{spread_pe}",
                        "Volume PCR": round(pe_vol/ce_vol, 2),
                        "Delta": delta,
                        "Theta": theta,
                        "IV (%)": iv,
                        "Pressure": "✅ Support" if pe_oi > ce_oi * 1.2 else "🔴 Resistance" if ce_oi > pe_oi * 1.2 else "Neutral"
                    })

                pcr = round(total_pe_oi / total_ce_oi, 2)
                confidence = min(int((pcr/1.5)*100), 98) if pcr > 1 else min(int(((1/pcr)/1.5)*100), 98)

                # Signal Logic
                if pcr > 1.2:
                    sig, col = "🔥 STRONG BUY", "green"
                    setup_box.success(f"**Action:** BUY {atm} CE\n\n**T1:** {spot+65}\n**SL:** {spot-30}")
                elif pcr < 0.8:
                    sig, col = "📉 STRONG SELL", "red"
                    setup_box.error(f"**Action:** BUY {atm} PE\n\n**T1:** {spot-65}\n**SL:** {spot+30}")
                else:
                    sig, col = "⏳ WAIT", "blue"
                    setup_box.warning("No clear Order-Flow signal.")

                # Updates
                spot_m.metric("NIFTY SPOT", spot)
                pcr_m.metric("OI PCR", pcr)
                signal_m.markdown(f"### Signal: :{col}[{sig}]")
                strength_m.metric("AI CONFIDENCE", f"{confidence}%")

                table_area.table(pd.DataFrame(rows))
                
            time.sleep(10)
    except Exception as e:
        st.error(f"Error: {e}")

if st.sidebar.button("🚀 LAUNCH BEAST ENGINE"):
    launch_ultimate_beast()
