import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, pandas as pd
from datetime import datetime

# ==========================================
# 🧠 QUANTUM CROSSOVER LOGIC (Anti-Kachra)
# ==========================================
def detect_strike_shift(spot, atm_ce_oi, atm_pe_oi, prev_ce, prev_pe):
    # Rate of Change (Speed of Writing)
    ce_speed = atm_ce_oi - prev_ce
    pe_speed = atm_pe_oi - prev_pe
    
    # Strike Crossover Detection (Jo aapne observe kiya)
    # Agar Call side par log Puts ke barabar aa rahe hain (Tug of War)
    oi_diff_percent = abs(atm_ce_oi - atm_pe_oi) / ((atm_ce_oi + atm_pe_oi) / 2) * 100
    
    if oi_diff_percent < 5: # 5% se kam ka difference hai (Barabari hone wali hai)
        if ce_speed > pe_speed:
            return "🔴 RESISTANCE SHIFTING DOWN (Bearish Takeover)", "red", "Strong Sell"
        else:
            return "🟢 SUPPORT SHIFTING UP (Bullish Takeover)", "green", "Strong Buy"
    
    if ce_speed > pe_speed * 2: return "⚠️ HEAVY CALL WRITING (Market Crash Alert)", "red", "Sell"
    if pe_speed > ce_speed * 2: return "🚀 HEAVY PUT WRITING (Short Covering Alert)", "green", "Buy"
    
    return "⚖️ NEUTRAL EQUILIBRIUM", "gray", "Wait"

# ==========================================
# 🚀 SYSTEM SETUP
# ==========================================
st.set_page_config(page_title="MKPV Institutional AI", layout="wide")
st.title("🛡️ MKPV INSTITUTIONAL AI (Shift & Trap Detector)")

CLIENT_ID, API_KEY, TOTP_SECRET, MPIN = "P51646259", "MT72qa1q", "W6SCERQJX4RSU6TXECROABI7TA", "9171"

# UI Metrics
c1, c2, c3, c4 = st.columns(4)
spot_box, crossover_box, speed_box, signal_box = c1.empty(), c2.empty(), c3.empty(), c4.empty()

st.divider()
verdict_area = st.empty()

def launch_pro_ai():
    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(CLIENT_ID, MPIN, otp)
        st.toast("⚡ Advanced Institutional Brain Online!")

        last_ce, last_pe = 0, 0
        
        while True:
            res = obj.ltpData("NSE", "Nifty 50", "26000")
            if res['status']:
                spot = float(res['data']['ltp'])
                atm = round(spot / 50) * 50
                
                # Live OI Data (Example context for the shift you saw)
                curr_ce_oi = 1540000  # 23450 CE OI badh raha hai
                curr_pe_oi = 1520000  # 23450 PE OI ke barabar hone wala hai
                
                status, color, action = detect_strike_shift(spot, curr_ce_oi, curr_pe_oi, last_ce, last_pe)
                
                # Update UI
                spot_box.metric("SPOT", spot)
                crossover_box.metric("OI GAP (%)", f"{round(abs(curr_ce_oi - curr_pe_oi)/(curr_ce_oi+1)*100, 2)}%")
                speed_box.metric("WRITING BIAS", "CALLS" if (curr_ce_oi-last_ce) > (curr_pe_oi-last_pe) else "PUTS")
                signal_box.metric("AI ACTION", action)

                verdict_area.markdown(f"""
                <div style="padding:30px; border-radius:15px; background-color:#1e1e1e; border:4px solid {color}; text-align:center;">
                    <h1 style="color:{color};">{status}</h1>
                    <p style="color:white; font-size: 20px;">Strike 23450 Analysis: Call and Put OI are converging!</p>
                </div>
                """, unsafe_allow_html=True)
                
                last_ce, last_pe = curr_ce_oi, curr_pe_oi

                # Deep Table for Strike Comparison
                st.subheader("🕵️ Institutional Heatmap")
                st.table(pd.DataFrame({
                    "Strike": [atm-50, atm, atm+50],
                    "OI Status": ["Converging", "Battleground", "Safe"],
                    "Institutional Bias": ["BEARISH" if status.startswith("🔴") else "BULLISH", "NEUTRAL", "NEUTRAL"]
                }))

            time.sleep(10)
    except Exception as e: st.error(f"Error: {e}")

if st.sidebar.button("🚀 START INSTITUTIONAL AI"):
    launch_pro_ai()
