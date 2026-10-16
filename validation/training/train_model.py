import numpy as np
import pandas as pd
import joblib
import json
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

FEATURES = [
    "unit_price_cv",
    "quantity_cv",
    "max_line_item_fraction",
    "num_line_items"
]

def train():
    # ── 1. Load the synthetic dataset ──────────────────────────────────
    df = pd.read_csv("training_data.csv")

    X = df[FEATURES].values       
    y = df["is_anomaly"].values  
    # ── 2. Scale the features ──────────────────────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── 3. Train Isolation Forest ──────────────────────────────────────
    model = IsolationForest(
        n_estimators=200,
        contamination=0.07,
        random_state=42
    )
    model.fit(X_scaled)

    # ── 4. Evaluate informally ─────────────────────────────────────────
    raw_predictions = model.predict(X_scaled)

    converted_predictions = np.where(raw_predictions == -1, 1, 0)

    print("=== Informal evaluation on training data ===")
    print(classification_report(y, converted_predictions, target_names=["normal", "anomaly"]))

    # ── 5. Save model and scaler ───────────────────────────────────────
    joblib.dump(model, "model.joblib")
    joblib.dump(scaler, "scaler.joblib")

    # ── 6. Save feature list ───────────────────────────────────────────
    with open("features.json", "w") as f:
        json.dump(FEATURES, f)

    print("Saved: model.joblib, scaler.joblib, features.json")

if __name__ == "__main__":
    train()