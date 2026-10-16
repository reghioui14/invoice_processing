def get_status_badge(status: str, validation_reason: str = "") -> str:
    """
    Validation Status badges:
    - Flagged: Bold & bright alerts (Tier 1 Red, Tier 2 Yellow, Tier 3 Orange)
    - Approved / Auto-Approved: Subdued, quiet neutral badges (No action needed)
    """
    status_clean = str(status or "").strip().lower().replace("-", "_")
    reason_lower = str(validation_reason or "").lower()

   
    if status_clean == "approved":
        return (
            '<span style="background:#1e293b;color:#86efac;padding:3px 9px;'
            'border-radius:12px;font-size:11px;font-weight:500;'
            'border:1px solid #334155;">✓ approved</span>'
        )
    elif status_clean == "auto_approved":
        return (
            '<span style="background:#1e293b;color:#86efac;padding:3px 9px;'
            'border-radius:12px;font-size:11px;font-weight:500;'
            'border:1px solid #334155;">✓✓approved</span>'
        )


    

    elif status_clean == "flagged":
        tier_color = _tier_color(reason_lower)

        return (
            f'<span style="background:{tier_color};color:white;padding:2px 8px;'
            f'border-radius:6px;font-size:11px;font-weight:600;">⚑ flagged</span>'
        )
    return (
        f'<span style="background:#374151;color:#9ca3af;padding:3px 9px;'
        f'border-radius:12px;font-size:11px;">{status or "Unknown"}</span>'
    )


def _tier_color(reason_lower: str) -> str:
    if "certain" in reason_lower:
        return "#ab1e1e"          # Rouge vif — Tier 1 (Règles)
    if "consistency" in reason_lower:
        return "#9eb50d"          # Jaune/Or — Tier 2 (ML)
    if "vendor pattern" in reason_lower or "vendor_pattern" in reason_lower:
        return "#c27d16"          # Orange — Tier 3 (Pattern Fournisseur)
    return "#dc2626"




def payment_badge(payment_status: str) -> str:
    """
    Payment Status badges (PRIMARY FOCUS):
    - Unpaid: High-contrast Amber/Orange (Action required!)
    - Paid: Calm, muted green (Settled)
    """
    pay_clean = str(payment_status or "").strip().lower()

    if pay_clean == "paid":
        return (
            '<span style="background:#1e293b;color:#86efac;padding:3px 9px;'
                        'border-radius:12px;font-size:11px;font-weight:500;'
                        'border:1px solid #334155;">✓ paid</span>'
        )
    
    # UNPAID : Badge éclatant ambre/jaune pour sauter aux yeux immédiatement
    return (
        '<span style="background:#f59e0b;color:#0f172a;padding:3px 10px;'
        'border-radius:10px;font-size:11px;font-weight:700;'
        'box-shadow:0 0 6px #f59e0b66;">⏳ UNPAID</span>'
    )


GLOBAL_CSS = """
<style>
    .block-container { padding-top: 1.5rem; }

    .invoice-row {
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #1f2937;
        margin-bottom: 6px;
        background: #111827;
        cursor: pointer;
        transition: background 0.15s;
    }
    .invoice-row:hover { background: #1f2937; }

    .detail-panel {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 24px;
        margin-top: 10px;
    }

    .section-title {
        color: #9ca3af;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }

    hr.subtle {
        border: none;
        border-top: 1px solid #1f2937;
        margin: 16px 0;
    }
</style>
"""