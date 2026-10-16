import numpy as np
from typing import Optional
from .models import InvoiceInput

def extract_features(invoice: InvoiceInput) -> Optional[dict]:
    """
    Transform a raw invoice into the 4 features
    that Isolation Forest was trained on.

    Returns None if the invoice doesn't have enough
    line item data to compute meaningful features
    (e.g., no line items at all).
    """

    # ── Guard: need at least 1 line item with valid data ───────────────
    if not invoice.line_items or len(invoice.line_items) == 0:
        return None

    # ── Extract raw arrays from line items ─────────────────────────────
    unit_prices = np.array([
        item.unit_price
        for item in invoice.line_items
        if item.unit_price is not None
    ], dtype=float)

    quantities = np.array([
        item.quantity
        for item in invoice.line_items
        if item.quantity is not None
    ], dtype=float)

    # ── Guard: need at least 1 valid price and quantity ────────────────
    if len(unit_prices) == 0 or len(quantities) == 0:
        return None

    # ── Compute line item totals ────────────────────────────────────────
    # Use the minimum length in case some items have price but no quantity
    min_len = min(len(unit_prices), len(quantities))
    line_totals = unit_prices[:min_len] * quantities[:min_len]
    total_from_items = float(np.sum(line_totals))

    # ── Feature 1: unit_price_cv ────────────────────────────────────────
    # How spread out are unit prices within this invoice?
    # Only meaningful with 2+ items (std of 1 item is always 0)
    if len(unit_prices) > 1 and np.mean(unit_prices) > 0:
        unit_price_cv = float(np.std(unit_prices) / np.mean(unit_prices))
    else:
        unit_price_cv = 0.0

    # ── Feature 2: quantity_cv ──────────────────────────────────────────
    # How spread out are quantities within this invoice?
    if len(quantities) > 1 and np.mean(quantities) > 0:
        quantity_cv = float(np.std(quantities) / np.mean(quantities))
    else:
        quantity_cv = 0.0

    # ── Feature 3: max_line_item_fraction ──────────────────────────────
    # Does one item dominate the invoice total?
    if total_from_items > 0 and len(line_totals) > 0:
        max_line_item_fraction = float(np.max(line_totals) / total_from_items)
    else:
        max_line_item_fraction = 0.0

    # ── Feature 4: num_line_items ───────────────────────────────────────
    # How many line items does this invoice have?
    num_line_items = len(invoice.line_items)

    return {
        "unit_price_cv": unit_price_cv,
        "quantity_cv": quantity_cv,
        "max_line_item_fraction": max_line_item_fraction,
        "num_line_items": num_line_items
    }