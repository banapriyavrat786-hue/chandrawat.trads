import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, requests, pandas as pd, numpy as np
from datetime import datetime
from scipy.stats import norm

# ==========================================
# 1. DYNAMIC FULL CHAIN MAPPER
# ==========================================
@st.cache_data(ttl=43200)
def get_angel_token_map():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        nifty_df = df[(df['name'] == 'NIFTY') & (df['exch_seg'] == 'NFO') & (df['instrumenttype'] == 'OPTIDX')].copy()
        nifty_df['expiry_date'] = pd.to_datetime(nifty_df['expiry'], format='%d%b%Y', errors='coerce')
        nifty_df['strike_float'] = pd.to_numeric(nifty_df['strike'], errors='coerce') 
        return nifty_df
    except: return pd.DataFrame()

def get_full_chain_tokens(nifty_df, spot_price, range_strikes=5):
    atm = round(spot_price / 50) * 50
    today = pd.Timestamp.now().normalize()
    future_expiries = nifty_df[nifty_df['expiry_date'] >= today]
    if future_expiries.empty: return []
    
    nearest_expiry = future_expiries.sort_values('expiry_date').iloc[0]['expiry_date']
    current_chain = nifty_df[nifty_df['expiry_date'] == nearest_expiry]
    
    chain_data = []
    # ATM +/- range_strikes (e.g., 5 strikes up and down)
    for i in range(-range_strikes, range_strikes + 1):
        strike = atm + (i * 50)
        target_val = float(strike * 100)
        try:
            ce = current_chain[(current_chain['strike_float'] == target_val) & (current_chain['symbol'].str.endswith('CE'))].iloc[0]
            pe = current_chain[(current_chain['strike_float'] == target_val) & (current_chain['symbol'].str.endswith('PE'))].iloc[0]
            chain_data.append({'strike': strike, 'ce_token': ce['token'], 'ce_symbol': ce['symbol'], 
                               'pe_token': pe['token'], 'pe_symbol': pe['symbol']})
        except: continue
    return chain_data

# ==========================================
# 2. BEAST ANALYSIS ENGINE
# ==========================================
class FullChainBrain:
    def __init__(self):
        self.r = 0.07

    def calculate_greeks(self, S, K, T, market_price, type="CE"):
        # Newton-Raphson for Live IV
        sigma = 0.18
        for _ in range(20):
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            price = S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2) if type == "CE" else K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            vega = S * norm.pdf(d1) * np.sqrt(T)
            diff = market_price - price
            if abs(diff) < 1e-4 or vega == 0: break
            sigma += diff / vega
        
        iv = max(sigma, 0.01)
        delta = norm.cdf(d1) if type == "CE" else norm.cdf(d1) - 1
        gamma = norm.pdf(d1) / (S * iv * np.sqrt(T))
        return round(delta, 2), round(iv * 100, 2), round(gamma, 6)

# ==========================================
# 3. UI DASHBOARD
# ==========================================
st.set_page_config(page_title="MKPV Full-Chain Beast", layout="wide")
st.markdown("<h1 style='text-align: center; color: #ff00ff;'>🧠 MKPV FULL-CHAIN QUANT BEAST v13.0</h1>", unsafe_allow_html=True)

# Main Stats
c1, c2, c3 = st.columns(3)
spot_ui = c1.empty()
net_gex_ui = c2.empty()
verdict_ui = c3.empty()

st.divider()
chain_table_ui = st.empty()

def start_full_chain_engine():
    brain = FullChainBrain()
    # ----------------------------------------
    CLIENT_ID, API_KEY, TOTP_SECRET, MPIN = "P51646259", "MT72qa1q", "W6SCERQJX4RSU6TXECROABI7TA", "9171"
    # ----------------------------------------
    
    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        obj.generateSession(CLIENT_ID, MPIN, otp)
        
        token_df = get_angel_token_map()
        
        while True:
            res_spot = obj.ltpData("NSE", "Nifty 50", "26000")
            if res_spot['status']:
                spot = float(res_spot['data']['ltp'])
                full_chain = get_full_chain_tokens(token_df, spot)
                
                rows = []
                total_gex = 0
                
                for strike in full_chain:
                    # Fetching CE & PE Prices
                    ce_ltp = float(obj.ltpData("NFO", strike['ce_symbol'], strike['ce_token'])['data']['ltp'])
                    pe_ltp = float(obj.ltpData("NFO", strike['pe_symbol'], strike['pe_token'])['data']['ltp'])
                    
                    ce_delta, ce_iv, ce_gamma = brain.calculate_greeks(spot, strike['strike'], 0.01, ce_ltp, "CE")
                    pe_delta, pe_iv, pe_gamma = brain.calculate_greeks(spot, strike['strike'], 0.01, pe_ltp, "PE")
                    
                    # GEX Calculation (Simplified for UI)
                    strike_gex = (ce_gamma - pe_gamma) * 1000000 
                    total_gex += strike_gex
                    
                    rows.append({
                        "Strike": strike['strike'],
                        "CE Price": ce_ltp, "CE Delta": ce_delta, "CE IV": ce_iv,
                        "Net GEX": round(strike_gex, 2),
                        "PE Price": pe_ltp, "PE Delta": pe_delta, "PE IV": pe_iv
                    })
                
                # UI Updates
                spot_ui.metric("NIFTY SPOT", f"₹{spot}")
                net_gex_ui.metric("TOTAL NET GEX", f"{round(total_gex, 2)}M", 
                                  delta="Bullish" if total_gex > 0 else "Bearish")
                
                # Beast Verdict
                if total_gex > 50 and spot > full_chain[0]['strike']:
                    verdict_ui.success("🔥 SIGNAL: STRONG BUY (Full Chain Support)")
                elif total_gex < -50:
                    verdict_ui.error("📉 SIGNAL: STRONG SELL (Full Chain Resistance)")
                else:
                    verdict_ui.warning("⏳ NEUTRAL (Wait for GEX Breakout)")

                chain_table_ui.table(pd.DataFrame(rows))
                
            time.sleep(10)
    except Exception as e: st.error(f"Error: {e}")

if st.sidebar.button("🚀 LAUNCH FULL-CHAIN ENGINE"):
    start_full_chain_engine()
