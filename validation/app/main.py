import importlib
FastAPI = importlib.import_module("fastapi").FastAPI
from .models import InvoiceInput, ValidationOutput, Reason
from .rules import apply_rule_based_checks
from .ml_scoring import score_invoice as score_with_ml
from .vendor_stats import check_vendor_stats

app = FastAPI(title="Invoice Validation Service")

@app.post("/tools/validate-invoice", response_model=ValidationOutput)
def validate_invoice(invoice: InvoiceInput):
    reasons = []

    # Tier 1: rules (required fields, confidence, ceiling, date, mismatch)
    reasons.extend(apply_rule_based_checks(invoice))

    # Tier 2: ML consistency model
    ml_reason = score_with_ml(invoice)
    if ml_reason:
        reasons.append(ml_reason)

    # Tier 3: vendor-specific historical pattern
    vendor_reason = check_vendor_stats(invoice)
    if vendor_reason:
        reasons.append(vendor_reason)

    is_flagged = len(reasons) > 0 

    return ValidationOutput(
        status="flagged" if is_flagged else "auto_approved",
        reasons=reasons if reasons else [Reason(tier="none", message="No issues detected")]
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}