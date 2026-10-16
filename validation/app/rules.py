from datetime import datetime, date
from .models import InvoiceInput, Reason


MIN_CONFIDENCE = 0.80

REQUIRED_FIELDS = ["vendor_name", "invoice_number", "invoice_date", "total_amount"]


def apply_rule_based_checks(invoice: InvoiceInput) -> list[Reason]:

    reasons: list[Reason] = []

    # ── Required fields ──────────────────────────────────────────────
    missing = [
        field for field in REQUIRED_FIELDS
        if getattr(invoice, field) in (None, "")
    ]
    if missing:
        reasons.append(Reason(
            tier="certain",
            message=f"Missing required field(s): {', '.join(missing)}"
        ))

    # ── Confidence ────────────────────────────────────────────────────
    score = invoice.confidence_score
    if score is None or score < MIN_CONFIDENCE:
        reasons.append(Reason(
            tier="certain",
            message=f"Confidence score below {MIN_CONFIDENCE}: {score if score is not None else 'missing'}"
        ))



    # ── Non-positive amount ───────────────────────────────────────────
    if invoice.total_amount is not None and invoice.total_amount <= 0:
        reasons.append(Reason(
            tier="certain",
            message=f"total_amount is non-positive ({invoice.total_amount})"
        ))

    # ── Future-dated invoice ──────────────────────────────────────────
    if invoice.invoice_date:
        try:
            parsed_date = datetime.strptime(invoice.invoice_date, "%Y-%m-%d").date()
            if parsed_date > date.today():
                reasons.append(Reason(
                    tier="certain",
                    message=f"invoice_date ({invoice.invoice_date}) is in the future"
                ))
        except ValueError:
            reasons.append(Reason(
                tier="certain",
                message=f"invoice_date ({invoice.invoice_date}) is not a valid YYYY-MM-DD date"
            ))

    # ── Total calculation ─────────────────────────────────────────────
    if invoice.line_items and invoice.total_amount is not None:
        line_items_total = sum(
            (item.quantity or 1) * (item.unit_price or 0)
            for item in invoice.line_items
        )

        expected_total = (
            line_items_total
            + (invoice.adjustments_total or 0)
        )

        if round(expected_total, 2) != round(invoice.total_amount, 2):
            reasons.append(Reason(
                tier="certain",
                message=(
                    f"Total mismatch: calculated total ({expected_total:.2f}) "
                    f"does not equal invoice total ({invoice.total_amount:.2f})"
                )
            ))

    return reasons