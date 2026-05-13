import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, pandas as pd, math
from datetime import datetime
from scipy.stats import norm

# Page Config
st.set_page_config(page_title="MKPV Pro AI Trader", layout="wide")
st.title("🧠 MKPV AI Trading Brain (PRO v2.0)")

# --- Credentials ---
CLIENT_ID = "P51646259"
API_KEY = "MT72qa1q"
TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
MPIN = "9171" # <-- PIN dalo

# Greeks Formula (Black-Scholes)
def get_delta(S, K, T, r, sigma):
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return round(norm.cdf(d1), 2)

# UI
m1, m2, m3 = st.columns(3)
spot_metric = m1.empty()
pcr_metric = m2.empty()
signal_metric = m3.empty()

st.divider()
st.subheader("🔥 Live Strike-wise Pressure & Greeks Analysis")
table_placeholder = st.empty()

def run_pro_engine():
    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(CLIENT_ID, MPIN, otp)
        st.toast("✅ Pro AI Engine Active!")
        
        while True:
            res = obj.ltpData("NSE", "Nifty 50", "26000")
            if res['status'] and res['data']:
                spot = float(res['data']['ltp'])
                atm = round(spot / 50) * 50
                
                # Pro Logic: Har strike ka analysis
                strikes_data = []
                total_ce_oi, total_pe_oi = 0, 0
                
                # ATM ke aas-paas ki 5 strikes ka Loop
                for s in range(atm-100, atm+150, 50):
                    # Placeholder for real OI/Vol fetch (requires tokens)
                    ce_oi = 1000000 + (s - atm) * 100
                    pe_oi = 1200000 - (s - atm) * 100
                    total_ce_oi += ce_oi
                    total_pe_oi += pe_oi
                    
                    delta = get_delta(spot, s, 0.02, 0.07, 0.15)
                    
                    strikes_data.append({
                        "Strike": s,
                        "Type": "ATM" if s == atm else ("OTM" if s > atm else "ITM"),
                        "Delta": delta,
                        "Pressure": "🔵 Neutral" if abs(ce_oi - pe_oi) < 50000 else ("🟢 Support" if pe_oi > ce_oi else "🔴 Resistance")
                    })

                pcr = round(total_pe_oi / total_ce_oi, 2)
                
                # Signal Logic
                if pcr > 1.15: sig, col = "🚀 BUY CALL", "green"
                elif pcr < 0.85: sig, col = "📉 BUY PUT", "red"
                else: sig, col = "⏳ SIDEWAYS", "blue"

                # Update UI
                spot_metric.metric("LIVE SPOT", f"₹{spot}")
                pcr_metric.metric("PCR RATIO", pcr)
                signal_metric.markdown(f"### Signal: :{col}[{sig}]")
                
                df = pd.DataFrame(strikes_data)
                table_placeholder.table(df)

            time.sleep(20)
    except Exception as e:
        st.error(f"Error: {e}")

if st.sidebar.button("🔥 Launch Pro Engine"):
    run_pro_engine()
