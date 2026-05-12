import streamlit as st
from SmartApi import SmartConnect
import pyotp, time
from datetime import datetime

# Page Setup
st.set_page_config(page_title="MKPV Trading App", layout="wide")
st.title("📊 MKPV Professional Trading Dashboard")

# --- Credentials ---
CLIENT_ID = "P51646259"
API_KEY = "MT72qa1q"
TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
MPIN = "9171" # <-- Apna PIN yahan sahi se dalo

# UI Placeholders
spot_box = st.empty()

def run_app():
    try:
        # Login Logic
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        session = obj.generateSession(CLIENT_ID, MPIN, otp)
        
        if session.get('status'):
            st.success("✅ Connected to Angel One!")
            
            while True:
                # Live Data Fetching with Safety Check
                res = obj.ltpData("NSE", "Nifty 50", "26000")
                
                if res and res.get('status') and res.get('data'):
                    spot = res['data'].get('ltp', 'N/A')
                    spot_box.metric("NIFTY SPOT", f"₹{spot}")
                else:
                    # Agar market band hai ya data nahi aa raha
                    spot_box.warning("😴 Market is currently Closed or API is Idle.")
                    st.info("Data will automatically resume tomorrow at 9:15 AM.")
                    break # Loop stop kar do raat ke liye
                
                time.sleep(30)
        else:
            st.error(f"❌ Login Failed: {session.get('message')}")
            
    except Exception as e:
        st.error(f"⚠️ System Note: {e}")

if st.sidebar.button("🚀 Start Live Feed"):
    run_app()
