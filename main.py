import streamlit as st
from SmartApi import SmartConnect
import pyotp, pandas as pd, requests, time, math
from datetime import datetime
from scipy.stats import norm
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page Setup
st.set_page_config(page_title="MKPV Trading App", layout="wide")
st.title("📊 MKPV Professional Trading Dashboard")

# --- Login Details (Baad mein Secrets mein dalenge) ---
CLIENT_ID = "P51646259"
API_KEY = "MT72qa1q"
TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
MPIN = "YOUR_PIN" # <-- Apna PIN yahan dalo

# Greeks Logic
def get_greeks(S, K, T, r, sigma, option_type="CE"):
    try:
        if T <= 0 or sigma <= 0: return 0, 0, 0
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        if option_type == "CE":
            delta = norm.cdf(d1)
            theta = -(S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))) - r * K * math.exp(-r * T) * norm.cdf(d2)
        else:
            delta = norm.cdf(d1) - 1
            theta = -(S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))) + r * K * math.exp(-r * T) * norm.cdf(-d2)
        return round(delta, 3), round(theta, 2), 0 # Gamma placeholder
    except: return 0, 0, 0

# Dashboard Layout
c1, c2, c3, c4 = st.columns(4)
spot_box = c1.empty()
vix_box = c2.empty()
pcr_box = c3.empty()
trend_box = c4.empty()

# Engine
def run_app():
    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(CLIENT_ID, MPIN, otp)
        st.success("✅ Connected to Angel One!")
        
        while True:
            # Live Data Fetching
            res_spot = obj.ltpData("NSE", "Nifty 50", "26000")
            res_vix = obj.ltpData("NSE", "INDIA VIX", "26017")
            
            spot = float(res_spot['data']['ltp'])
            vix = float(res_vix['data']['ltp'])
            
            # Simple Dashboard Update
            spot_box.metric("NIFTY SPOT", f"₹{spot}")
            vix_box.metric("INDIA VIX", f"{vix}")
            pcr_box.metric("PCR", "Calculating...")
            
            time.sleep(30) # 30 seconds refresh
    except Exception as e:
        st.error(f"Error: {e}")

if st.sidebar.button("🚀 Start Live Feed"):
    run_app()
