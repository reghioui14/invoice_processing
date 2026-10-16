import numpy as np
from .models import InvoiceInput, Reason
from .db import get_connection

MIN_HISTORY_FOR_STATS = 15
Z_SCORE_THRESHOLD = 3
TOLERANCE_PCT = 0.05   

def check_vendor_stats(invoice: InvoiceInput) -> Reason | None:
  

    if not invoice.vendor_name or invoice.total_amount is None:
        return None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT i.total_amount
            FROM invoices i
            JOIN vendors v ON i.vendor_id = v.id
            WHERE v.name = %s 
              AND i.status IN ('auto_approved', 'approved')
            """,
            (invoice.vendor_name,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        return None

    amounts = np.array(
        [row[0] for row in rows if row[0] is not None],
        dtype=float
    )

    if len(amounts) < MIN_HISTORY_FOR_STATS:
        return None

    mean = float(np.mean(amounts))
    std = float(np.std(amounts))

    if std == 0:
        if abs(invoice.total_amount - mean) > mean * TOLERANCE_PCT:
            return Reason(
                tier="vendor_pattern",
                message=(
                    f"{invoice.vendor_name}: this invoice (${invoice.total_amount:.2f}) "
                    f"differs from vendor's consistent historical amount (${mean:.2f})"
                )
            )
        return None

    z_score = (invoice.total_amount - mean) / std

    if abs(z_score) > Z_SCORE_THRESHOLD:
        direction = "higher" if z_score > 0 else "lower"
        return Reason(
            tier="vendor_pattern",
            message=(
                f"{invoice.vendor_name}: this invoice (${invoice.total_amount:.2f}) is "
                f"unusually {direction} than vendor's historical average "
                f"(${mean:.2f} ± ${std:.2f})"
            )
        )

    return None