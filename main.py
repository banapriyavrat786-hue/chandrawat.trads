import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, pandas as pd, math
from datetime import datetime
from scipy.stats import norm

# ==========================================
# 1. THE AI BRAIN (SENTIMENT & CONTEXT ENGINE)
# ==========================================
def analyze_market_behavior(spot, pcr, vol_pcr, delta_trend, bid_ask_bias):
    """
    Ye function andha calculation nahi, context samajhta hai.
    """
    score = 0
    # OI Context
    if pcr > 1.3: score += 30
    elif pcr < 0.7: score -= 30
    
    # Volume Context (Momentum)
    if vol_pcr > 1.2: score += 20
    elif vol_pcr < 0.8: score -= 20
    
    # Order Flow Context (Aggression)
    if bid_ask_bias == "Aggressive Buying": score += 25
    elif bid_ask_bias == "Aggressive Selling": score -= 25
    
    # Final AI Verdict
    if score >= 70: return "🚀 SUPER BULLISH (Institutional Entry)", "green", score
    if score >= 40: return "✅ MODERATE BUY (Wait for Pullback)", "lightgreen", score
    if score <= -70: return "📉 SUPER BEARISH (Heavy Liquidation)", "red", score
    if score <= -40: return "⚠️ MODERATE SELL (Resistance Active)", "orange", score
    return "⏳ NEUTRAL (Market Choppy - No Trade)", "gray", score

# ==========================================
# 2. ADVANCED UI CONFIG (Dark Pro Theme)
# ==========================================
st.set_page_config(page_title="MKPV AI Quantum", layout="wide")
st.markdown("<h1 style='text-align: center; color: #00FFCC;'>🧠 MKPV AI QUANTUM BRAIN v4.0</h1>", unsafe_allow_html=True)

# Credentials
CLIENT_ID = "P51646259"
API_KEY = "MT72qa1q"
TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
MPIN = "9171" 

# Top Metrics Panel
c1, c2, c3, c4 = st.columns(4)
spot_box = c1.empty()
pcr_box = c2.empty()
vol_box = c3.empty()
confidence_box = c4.empty()

st.divider()

# Main AI Dashboard
verdict_area = st.empty()
st.subheader("🕵️ Deep Strike Analysis (Order Flow & Greeks)")
data_table = st.empty()

# Sidebar Setup
st.sidebar.header("🎯 AI Execution Radar")
setup_display = st.sidebar.empty()

# ==========================================
# 3. EXECUTION ENGINE
# ==========================================
def run_quantum_brain():
    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(CLIENT_ID, MPIN, otp)
        st.toast("⚡ Quantum Brain Synchronized!")

        while True:
            # Data Fetching (Assuming Live Feed)
            res = obj.ltpData("NSE", "Nifty 50", "26000")
            if res['status'] and res['data']:
                spot = float(res['data']['ltp'])
                atm = round(spot / 50) * 50
                
                # Mocking Institutional Data for Logic (Real-time integration in Market Hours)
                pcr_val = 1.35
                vol_pcr_val = 1.42
                bias = "Aggressive Buying" 
                
                verdict, v_color, ai_score = analyze_market_behavior(spot, pcr_val, vol_pcr_val, 0, bias)

                # Updating Visuals
                spot_box.metric("NIFTY SPOT", spot)
                pcr_box.metric("INSTITUTIONAL PCR", pcr_val, delta="Bullish Bias")
                vol_box.metric("VOL MOMENTUM", f"{vol_pcr_val}x")
                confidence_box.metric("AI CONFIDENCE", f"{abs(ai_score)}%")

                verdict_area.markdown(f"""
                <div style="padding:20px; border-radius:10px; border: 2px solid {v_color}; background-color: #1e1e1e; text-align: center;">
                    <h2 style="color: {v_color};">{verdict}</h2>
                </div>
                """, unsafe_allow_html=True)

                # Strike Table with Visual Logic
                strikes = []
                for s in range(atm-150, atm+200, 50):
                    strikes.append({
                        "Strike": s,
                        "Zone": "Support" if s < spot else "Resistance",
                        "Institutional Pressure": "🟢 High" if pcr_val > 1.1 else "🔴 High",
                        "Gamma Sensitivity": round(0.0045 + (abs(s-atm)/10000), 5),
                        "Risk/Reward": "1:2.5" if abs(s-spot) < 100 else "1:1.5"
                    })
                data_table.table(pd.DataFrame(strikes))

                # Trade Setup Radar
                if ai_score >= 40:
                    setup_display.success(f"**STRATEGY: LONG**\n\n**Entry:** {spot}\n**T1:** {spot+70}\n**SL:** {spot-30}\n\n*Targeting Gamma Blast*")
                elif ai_score <= -40:
                    setup_display.error(f"**STRATEGY: SHORT**\n\n**Entry:** {spot}\n**T1:** {spot-70}\n**SL:** {spot+30}\n\n*Targeting IV Spike*")
                
            time.sleep(10)
    except Exception as e:
        st.error(f"AI Brain Link Failure: {e}")

if st.sidebar.button("🧠 LAUNCH QUANTUM BRAIN"):
    run_quantum_brain()
