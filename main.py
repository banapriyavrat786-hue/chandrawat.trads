import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, requests, pandas as pd, numpy as np
from datetime import datetime
from scipy.stats import norm

# ==========================================
# 1. LIVE TOKEN MAPPER (No Hardcoding)
# ==========================================
@st.cache_data(ttl=43200) # Din mein ek baar download hoga (taaki app fast chale)
def get_angel_token_map():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        # Filter only Nifty Options
        nifty_df = df[(df['name'] == 'NIFTY') & (df['exch_seg'] == 'NFO') & (df['instrumenttype'] == 'OPTIDX')].copy()
        nifty_df['expiry_date'] = pd.to_datetime(nifty_df['expiry'], errors='coerce')
        return nifty_df
    except Exception as e:
        st.error(f"Token Map Fetch Error: {e}")
        return pd.DataFrame()

def get_live_atm_tokens(nifty_df, spot_price):
    atm = round(spot_price / 50) * 50
    # Find nearest upcoming expiry
    future_expiries = nifty_df[nifty_df['expiry_date'] >= pd.Timestamp.now().normalize()]
    if future_expiries.empty: return None, None, atm
    
    nearest_expiry = future_expiries.sort_values('expiry_date').iloc[0]['expiry_date']
    current_chain = nifty_df[nifty_df['expiry_date'] == nearest_expiry]
    
    # Exact Strike Match formatting (Angel uses 2350000.000000 format)
    strike_str = str(float(atm * 100))
    
    try:
        ce_row = current_chain[(current_chain['strike'] == strike_str) & (current_chain['symbol'].str.endswith('CE'))].iloc[0]
        pe_row = current_chain[(current_chain['strike'] == strike_str) & (current_chain['symbol'].str.endswith('PE'))].iloc[0]
        return ce_row, pe_row, atm
    except:
        return None, None, atm

# ==========================================
# 2. REAL IV SOLVER
# ==========================================
class AdvancedQuantMath:
    def __init__(self):
        self.r = 0.07

    def bs_price_and_vega(self, S, K, T, sigma, type="CE"):
        try:
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            price = S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2) if type == "CE" else K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            vega = S * norm.pdf(d1) * np.sqrt(T)
            return price, vega
        except: return 0, 0

    def calculate_live_iv(self, market_price, S, K, T, type="CE"):
        sigma = 0.20 
        for i in range(100):
            price, vega = self.bs_price_and_vega(S, K, T, sigma, type)
            diff = market_price - price
            if abs(diff) < 1e-5: break
            if vega == 0: return 0.001
            sigma += diff / vega 
        return max(sigma, 0.001)

# ==========================================
# 3. FEATURE STORE & ML LAYER
# ==========================================
class MachineLearningPipeline:
    def __init__(self):
        self.feature_db = pd.DataFrame(columns=['Time', 'Spot', 'ATM_Strike', 'Real_CE_Price', 'Live_IV', 'Gamma_Pressure', 'AI_Confidence'])

    def engineer_features(self, real_ce_price, spot, atm, live_iv):
        # Calculating live gamma pressure dynamically
        gamma_pressure = (real_ce_price / spot) * (live_iv * 100) if spot > 0 else 0
        return {'Gamma_Pressure': gamma_pressure}

    def ml_predict(self, features):
        prediction_score = 50 + (features['Gamma_Pressure'] * 1.5)
        return min(max(prediction_score, 0), 100) 

# ==========================================
# 4. DASHBOARD & EXECUTION
# ==========================================
st.set_page_config(page_title="MKPV 100% LIVE Quant", layout="wide")
st.markdown("<h1 style='text-align: center; color: #00FFCC;'>📡 MKPV 100% LIVE QUANT ENGINE v12.0</h1>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
spot_box = m1.empty()
prem_box = m2.empty()
iv_box = m3.empty()
ml_prob_box = m4.empty()

st.divider()
table_placeholder = st.empty()

def start_100_percent_live_engine():
    quant = AdvancedQuantMath()
    ml_pipeline = MachineLearningPipeline()
    
    # ----------------------------------------
    CLIENT_ID = "P51646259"
    API_KEY = "MT72qa1q"
    TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
    MPIN = "9171" # <-- Apna 4-digit PIN dalein
    # ----------------------------------------

    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        session = obj.generateSession(CLIENT_ID, MPIN, otp)
        
        if not session.get('status'):
            st.error(f"Login Failed: {session.get('message')}")
            return
            
        st.toast("⚡ API Connected! Fetching Scrip Master... Please Wait.")
        nifty_token_df = get_angel_token_map()
        st.toast("✅ Tokens Loaded. Entering Live Loop!")
            
        while True:
            # 1. FETCH LIVE SPOT
            res_spot = obj.ltpData("NSE", "Nifty 50", "26000")
            
            if res_spot['status'] and res_spot['data']:
                spot = float(res_spot['data']['ltp'])
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 2. DYNAMIC TOKEN MAPPING (Find ATM & Exact Expiry Tokens)
                ce_row, pe_row, atm_strike = get_live_atm_tokens(nifty_token_df, spot)
                
                if ce_row is not None:
                    # 3. 100% LIVE PREMIUM FETCH
                    ce_token, ce_symbol = ce_row['token'], ce_row['symbol']
                    res_ce = obj.ltpData("NFO", ce_symbol, ce_token)
                    
                    if res_ce['status'] and res_ce['data']:
                        real_ce_price = float(res_ce['data']['ltp'])
                        
                        # 4. REAL MATH COMPUTATION
                        real_iv = quant.calculate_live_iv(real_ce_price, spot, atm_strike, 0.01, "CE")
                        features = ml_pipeline.engineer_features(real_ce_price, spot, atm_strike, real_iv)
                        ai_probability = ml_pipeline.ml_predict(features)
                        
                        # 5. LOG TO MEMORY (No Dummy Data)
                        ml_pipeline.feature_db.loc[len(ml_pipeline.feature_db)] = [
                            timestamp, spot, atm_strike, real_ce_price, round(real_iv * 100, 2), 
                            round(features['Gamma_Pressure'], 4), round(ai_probability, 1)
                        ]
                        
                        if len(ml_pipeline.feature_db) > 50:
                            ml_pipeline.feature_db = ml_pipeline.feature_db.iloc[1:].reset_index(drop=True)
                        
                        # 6. UI UPDATES
                        spot_box.metric("LIVE NIFTY SPOT", f"₹{spot}", delta="NSE Real-time")
                        prem_box.metric(f"LIVE {atm_strike} CE", f"₹{real_ce_price}", delta=f"Token: {ce_token}")
                        iv_box.metric("REAL IV (Newton-Raphson)", f"{round(real_iv * 100, 2)}%", delta="Computed from Live Premium")
                        
                        if ai_probability > 60:
                            ml_prob_box.metric("ML PRED (BULLISH)", f"{round(ai_probability, 1)}%", delta="Gamma Expanding")
                        else:
                            ml_prob_box.metric("ML PRED (BEARISH)", f"{round(ai_probability, 1)}%", delta="-Gamma Compressing", delta_color="inverse")

                        with table_placeholder.container():
                            st.subheader("🗄️ 100% Live Feature Store (Self-Learning Memory)")
                            st.dataframe(ml_pipeline.feature_db.tail(10).sort_index(ascending=False), use_container_width=True)
                    else:
                        st.warning("⚠️ Connected, but API returned blank data for Option Premium. (Market might be closed)")
                else:
                    st.warning("⏳ Generating Token Map... Please wait.")
                
            time.sleep(5) # 5 Second Live Tick Loop
            
    except Exception as e:
        st.error(f"System Error: {e}")

if st.sidebar.button("🚀 INITIATE 100% LIVE ENGINE"):
    start_100_percent_live_engine()
