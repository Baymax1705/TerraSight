import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from database import SessionLocal, OfficialCircleRate, CachedRate

MODEL_PATH = os.path.join(os.path.dirname(__file__), "market_multiplier_model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "market_multiplier_scaler.joblib")

def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except:
        return default

def extract_training_data():
    """
    Extracts data from the DB to create training examples.
    We look for locations that have BOTH a CachedRate (MagicBricks listing)
    AND an OfficialCircleRate (Government rate) to compute the true multiplier.
    """
    db = SessionLocal()
    training_records = []
    try:
        # Get all cached market rates (our ground truth proxy for actual selling prices)
        market_rates = db.query(CachedRate).all()
        for market in market_rates:
            # Try to find a matching official rate to compute the target multiplier
            parts = [p.strip() for p in market.location_query.split(",") if len(p.strip()) > 2]
            official = None
            for part in parts:
                official = db.query(OfficialCircleRate).filter(
                    OfficialCircleRate.locality.ilike(f"%{part}%") |
                    OfficialCircleRate.district.ilike(f"%{part}%")
                ).first()
                if official: break
            
            if official and official.rate_sqm > 0 and market.estimated_rate_sqm > 0:
                # Target Variable: Actual Multiplier
                target_multiplier = float(market.estimated_rate_sqm) / float(official.rate_sqm)
                
                # Clip extreme outliers (e.g., data entry errors causing 50x multiplier)
                if target_multiplier < 0.5 or target_multiplier > 10.0:
                    continue
                    
                # Feature: Months since official publication
                # Make sure both datetimes are offset-naive for subtraction
                months_elapsed = (datetime.now() - official.effective_date).days / 30.0
                
                # Feature: District Tier encoding
                d_lower = official.district.lower()
                tier1 = ['noida', 'gb nagar', 'lucknow', 'ghaziabad', 'kanpur']
                tier2 = ['agra', 'meerut', 'varanasi', 'prayagraj', 'bareilly', 'gorakhpur']
                
                is_tier_1 = 1 if any(t in d_lower for t in tier1) else 0
                is_tier_2 = 1 if any(t in d_lower for t in tier2) else 0
                
                # In a full pipeline, we would query OSM here for spatial features.
                # For this implementation, we use proxy features available locally.
                
                training_records.append({
                    "months_elapsed": months_elapsed,
                    "is_tier_1": is_tier_1,
                    "is_tier_2": is_tier_2,
                    "base_govt_rate": float(official.rate_sqm),
                    "target_multiplier": target_multiplier
                })
    finally:
        db.close()
        
    return pd.DataFrame(training_records)

def train_model():
    """Trains the RandomForestRegressor to predict market multipliers."""
    print("🧠 Extracting training data from geointel.db...")
    df = extract_training_data()
    
    if len(df) < 10:
        print("⚠️ Not enough overlapping data (Govt + MagicBricks) to train ML model.")
        print("Continuing to use heuristic fallback until more Sentinel scans run.")
        return False

    print(f"✅ Found {len(df)} valid overlapping records. Training RandomForest...")
    
    X = df[["months_elapsed", "is_tier_1", "is_tier_2", "base_govt_rate"]]
    y = df["target_multiplier"]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # RandomForest handles non-linear data and outliers well without excessive tuning
    model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_scaled, y)
    
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("💾 ML Model and Scaler successfully saved!")
    return True

def predict_multiplier(district: str, govt_rate_sqm: float, effective_date: datetime) -> dict:
    """
    Inference Function: Predicts the dynamic market multiplier.
    Returns the predicted multiplier and a confidence score.
    """
    # 1. Fallback Logic (if model isn't trained yet)
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        # Return intelligent heuristic fallback
        d_lower = district.lower() if district else ""
        tier1 = ['noida', 'gb nagar', 'lucknow', 'ghaziabad', 'kanpur']
        tier2 = ['agra', 'meerut', 'varanasi', 'prayagraj', 'bareilly', 'gorakhpur']
        
        fallback_mult = 2.0 if any(t in d_lower for t in tier1) else (1.6 if any(t in d_lower for t in tier2) else 1.4)
        return {
            "predicted_multiplier": fallback_mult,
            "confidence": 0.3, # Low confidence because it's a static heuristic
            "is_ml_based": False
        }

    # 2. ML Inference
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        
        months_elapsed = (datetime.now() - effective_date).days / 30.0
        d_lower = district.lower() if district else ""
        tier1 = ['noida', 'gb nagar', 'lucknow', 'ghaziabad', 'kanpur']
        tier2 = ['agra', 'meerut', 'varanasi', 'prayagraj', 'bareilly', 'gorakhpur']
        
        is_tier_1 = 1 if any(t in d_lower for t in tier1) else 0
        is_tier_2 = 1 if any(t in d_lower for t in tier2) else 0
        
        X_infer = pd.DataFrame([{
            "months_elapsed": months_elapsed,
            "is_tier_1": is_tier_1,
            "is_tier_2": is_tier_2,
            "base_govt_rate": _safe_float(govt_rate_sqm)
        }])
        
        X_scaled = scaler.transform(X_infer)
        predicted_mult = float(model.predict(X_scaled)[0])
        
        # Clip to realistic bounds (never drop below 1.0, max 4.0)
        predicted_mult = max(1.0, min(predicted_mult, 4.0))
        
        # Confidence scoring based on age of data and if it matches known tiers
        confidence = 0.85
        if months_elapsed > 36: confidence -= 0.15
        if not is_tier_1 and not is_tier_2: confidence -= 0.10
        
        return {
            "predicted_multiplier": round(predicted_mult, 2),
            "confidence": round(max(0.4, confidence), 2),
            "is_ml_based": True
        }
        
    except Exception as e:
        print(f"ML Inference Error: {e}")
        # Graceful fallback
        return {"predicted_multiplier": 1.5, "confidence": 0.1, "is_ml_based": False}

if __name__ == "__main__":
    train_model()
