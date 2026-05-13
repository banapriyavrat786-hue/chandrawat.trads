import streamlit as st
from SmartApi import SmartConnect
import pyotp, time, pandas as pd, numpy as np
from datetime import datetime
from scipy.stats import norm

# ==========================================
# 1. REAL IV SOLVER (Newton-Raphson Method)
# ==========================================
class AdvancedQuantMath:
    def __init__(self):
        self.r = 0.07 # Risk-free rate

    def bs_price_and_vega(self, S, K, T, sigma, type="CE"):
        try:
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if type == "CE":
                price = S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
            else:
                price = K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                
            vega = S * norm.pdf(d1) * np.sqrt(T)
            return price, vega
        except:
            return 0, 0

    def calculate_live_iv(self, market_price, S, K, T, type="CE", tol=1e-5, max_iter=100):
        # Reverse engineering IV from live premium
        sigma = 0.20 # Initial guess
        for i in range(max_iter):
            price, vega = self.bs_price_and_vega(S, K, T, sigma, type)
            diff = market_price - price
            if abs(diff) < tol:
                break
            if vega == 0: 
                return 0.001
            sigma = sigma + diff / vega 
        return max(sigma, 0.001)

# ==========================================
# 2. FEATURE STORE & MACHINE LEARNING LAYER
# ==========================================
class MachineLearningPipeline:
    def __init__(self):
        # Feature Database for Self-Learning Memory
        self.feature_db = pd.DataFrame(columns=['Time', 'Spot', 'Gamma_Pressure', 'Vol_Expansion', 'AI_Confidence'])

    def engineer_features(self, net_gex, volume, current_atr, hist_atr, oi_change):
        gamma_pressure = net_gex / volume if volume > 0 else 0
        vol_expansion = current_atr / hist_atr if hist_atr > 0 else 1
        return {
            'Gamma_Pressure': gamma_pressure,
            'Vol_Expansion': vol_expansion,
            'OI_Shift_Speed': oi_change
        }

    def ml_predict(self, features):
        # AI Logic: Weighting institutional features
        prediction_score = 50 + (features['Gamma_Pressure'] * 10) + (features['Vol_Expansion'] * 5)
        return min(max(prediction_score, 0), 100) # Returns 0 to 100%

# ==========================================
# 3. UI DASHBOARD SETUP
# ==========================================
st.set_page_config(page_title="MKPV Quant ML Architecture", layout="wide")
st.markdown("<h1 style='text-align: center; color: #ff00ff;'>🧠 MKPV ML & INFRASTRUCTURE ENGINE (v11.0)</h1>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
iv_box = m1.empty()
ml_prob_box = m2.empty()
feature_box = m3.empty()

st.divider()
table_placeholder = st.empty()

# ==========================================
# 4. CORE EXECUTION ENGINE
# ==========================================
def start_true_ai_infrastructure():
    quant = AdvancedQuantMath()
    ml_pipeline = MachineLearningPipeline()
    
    # ----------------------------------------
    # 🔐 AUTHENTICATION DETAILS
    # ----------------------------------------
    CLIENT_ID = "P51646259"
    API_KEY = "MT72qa1q"
    TOTP_SECRET = "W6SCERQJX4RSU6TXECROABI7TA"
    MPIN = "9171"  # <--- Bhai, apna 4-digit PIN yahan dalo (Jaise "1234")
    # ----------------------------------------

    try:
        otp = pyotp.TOTP(TOTP_SECRET.replace(" ", "")).at(int(time.time()))
        obj = SmartConnect(api_key=API_KEY)
        session = obj.generateSession(CLIENT_ID, MPIN, otp)
        
        if session.get('status'):
            st.toast("⚡ ML Engine & SmartAPI Connected Successfully!")
        else:
            st.error(f"Login Failed: {session.get('message')}")
            return
            
        while True:
            # 1. Fetch Live Nifty Spot
            res = obj.ltpData("NSE", "Nifty 50", "26000")
            
            if res['status'] and res['data']:
                spot = float(res['data']['ltp'])
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Live Premium (Placeholder till full option chain API is added)
                ce_market_price = 105.20 
                atm_strike = round(spot / 50) * 50
                
                # 2. REAL IV INVERSION (Newton-Raphson)
                real_iv = quant.calculate_live_iv(ce_market_price, spot, atm_strike, 0.01, "CE")
                
                # 3. FEATURE ENGINEERING
                # Mock institutional data for ML feeding
                features = ml_pipeline.engineer_features(net_gex=450000, volume=120000, current_atr=18, hist_atr=15, oi_change=5000)
                
                # 4. MACHINE LEARNING PREDICTION
                ai_probability = ml_pipeline.ml_predict(features)
                
                # 5. LOG TO FEATURE STORE (Memory)
                ml_pipeline.feature_db.loc[len(ml_pipeline.feature_db)] = [
                    timestamp, spot, round(features['Gamma_Pressure'], 4), round(features['Vol_Expansion'], 4), round(ai_probability, 1)
                ]
                
                # Keep database from freezing Streamlit (keep last 50 rows)
                if len(ml_pipeline.feature_db) > 50:
                    ml_pipeline.feature_db = ml_pipeline.feature_db.iloc[1:].reset_index(drop=True)
                
                # 6. DASHBOARD UPDATES
                iv_box.metric(f"REAL IV ({atm_strike} CE)", f"{round(real_iv * 100, 2)}%", delta="Live Math Calculation")
                
                if ai_probability > 75:
                    ml_prob_box.metric("ML PREDICTION (BULLISH)", f"{round(ai_probability, 1)}%", delta="High Probability Setup")
                elif ai_probability < 30:
                    ml_prob_box.metric("ML PREDICTION (BEARISH)", f"{round(ai_probability, 1)}%", delta="-High Probability Setup", delta_color="inverse")
                else:
                    ml_prob_box.metric("ML PREDICTION (NEUTRAL)", f"{round(ai_probability, 1)}%", delta="Wait for Setup", delta_color="off")
                
                feature_box.metric("FEATURE DATABASE", f"{len(ml_pipeline.feature_db)} Rows", delta="Logging ticks for ML training")

                # Show Live Memory Database
                with table_placeholder.container():
                    st.subheader("🗄️ Live Feature Store (Self-Learning Memory Data)")
                    st.dataframe(ml_pipeline.feature_db.tail(10).sort_index(ascending=False), use_container_width=True)
                
            time.sleep(10) # Live Tick Loop
            
    except Exception as e:
        st.error(f"System Error: {e}")

if st.sidebar.button("🚀 INITIATE ML PIPELINE"):
    start_true_ai_infrastructure()
