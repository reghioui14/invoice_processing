import numpy as np
import joblib
import json
from pathlib import Path
from .models import InvoiceInput, Reason
from .feature_extraction import extract_features

TRAINING_DIR = Path(__file__).parent.parent / "training"
MODEL_PATH = TRAINING_DIR / "model.joblib"
SCALER_PATH = TRAINING_DIR / "scaler.joblib"
FEATURES_PATH = TRAINING_DIR / "features.json"

try:
    _model = joblib.load(MODEL_PATH)
    _scaler = joblib.load(SCALER_PATH)
    with open(FEATURES_PATH) as f:
        _features = json.load(f)
    _model_available = True
except FileNotFoundError:
    _model = None
    _scaler = None
    _features = None
    _model_available = False


def _raw_score_to_anomaly_score(raw_score: float) -> float:
    clipped = np.clip(raw_score, -0.7, 0.1)
    normalized = (clipped - 0.1) / (-0.7 - 0.1)
    return float(np.clip(normalized, 0.0, 1.0))


def score_invoice(invoice: InvoiceInput) -> Reason | None:
    if not _model_available:
        return None

    features = extract_features(invoice)
    if features is None:
        return None

    feature_vector = np.array([[features[f] for f in _features]])
    feature_vector_scaled = _scaler.transform(feature_vector)
    raw_score = float(_model.score_samples(feature_vector_scaled)[0])
    anomaly_score = _raw_score_to_anomaly_score(raw_score)

    if anomaly_score < 0.5:
        return None

    return Reason(
        tier="consistency",
        message=f"Statistical anomaly detected in line-item structure (score: {anomaly_score:.2f}) — manual review recommended"
    )