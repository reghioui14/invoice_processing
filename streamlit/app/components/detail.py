import os
import streamlit as st
from PIL import Image
from app.db import (
    fetch_invoice_by_id,
    fetch_line_items,
    mark_paid,
    approve_invoice,
    delete_invoice,
    correct_invoice,
)
from app.utils.styles import get_status_badge, payment_badge

FILES_BASE = os.getenv("FILES_BASE_PATH", "/files/invoices")


def render_detail(invoice_id: int, on_close, on_refresh):
    inv = fetch_invoice_by_id(invoice_id)
    if not inv:
        st.error("Invoice not found.")
        return

    line_items = fetch_line_items(invoice_id)
    status = inv["status"] or ""
    validation_str = (inv["validation_reason"] or "").lower()
    is_flagged = status == "flagged"

    if st.button("← Back to list"):
     on_close()
     return

    st.markdown("---")

    title_col, badge_col, pay_col = st.columns([3, 1.5, 1.2])
    title_col.markdown(f"## Invoice {inv['invoice_number'] or f'#{invoice_id}'}")
    badge_col.markdown(get_status_badge(status, validation_str), unsafe_allow_html=True)
    pay_col.markdown(payment_badge(inv["payment_status"] or "unpaid"), unsafe_allow_html=True)

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)

    left, right = st.columns([1.4, 1])

    with left:
        _render_info_section(inv)
        st.markdown("---")
        _render_line_items(line_items, inv["currency"])
        st.markdown("---")
        _render_validation_reasons(inv["validation_reason"])

    with right:
        _render_pdf_preview(inv["original_file_path"])

    st.markdown("---")
    _render_actions(inv, is_flagged, invoice_id, on_close, on_refresh)


def _render_info_section(inv):
    st.markdown("**Invoice Details**")
    fields = [
        ("Vendor",        inv["vendor_name"] or "Unknown"),
        ("Invoice #",     inv["invoice_number"] or "—"),
        ("Date",          str(inv["invoice_date"]) if inv["invoice_date"] else "—"),
        ("Currency",      inv["currency"] or "—"),
        ("Total Amount",  f"{inv['currency'] or ''} {float(inv['total_amount']):,.2f}"
                          if inv["total_amount"] is not None else "—"),
        ("Confidence",    f"{float(inv['confidence_score']) * 100:.0f}%"
                          if inv["confidence_score"] is not None else "—"),
        ("Created",       str(inv["created_at"])[:19] if inv["created_at"] else "—"),
        ("Paid At",       str(inv["paid_at"])[:19] if inv["paid_at"] else "—"),
    ]
    for label, value in fields:
        col_a, col_b = st.columns([1, 2])
        col_a.markdown(f'<p class="section-title">{label}</p>', unsafe_allow_html=True)
        col_b.markdown(f"**{value}**")


def _render_line_items(line_items, currency):
    st.markdown("**Line Items**")
    if not line_items:
        st.caption("No line items recorded.")
        return
    for item in line_items:
        desc = item["description"] or "—"
        qty = item["quantity"]
        price = item["unit_price"]
        qty_str = str(qty) if qty is not None else "—"
        price_str = f"{currency or ''} {float(price):,.2f}" if price is not None else "—"
        total_str = (
            f"{currency or ''} {float(qty) * float(price):,.2f}"
            if qty is not None and price is not None else "—"
        )
        st.markdown(
            f"- **{desc}** &nbsp;|&nbsp; Qty: {qty_str} &nbsp;|&nbsp; "
            f"Unit: {price_str} &nbsp;|&nbsp; Total: {total_str}",
            unsafe_allow_html=True,
        )


def _render_validation_reasons(validation_reason: str):
    """
    Parses the format: "[tier] message; [tier] message"
    e.g. "[certain] Missing required field(s): vendor_name; [consistency] ..."
    """
    st.markdown("**Validation Notes**")

    if not validation_reason or not validation_reason.strip():
        st.caption("None")
        return

    # Split on "; " to get individual reason entries
    entries = [e.strip() for e in validation_reason.split(";") if e.strip()]

    tier_colors = {
        "certain": "#dc2626",           # red
        "consistency": "#ca8a04",       # yellow
        "vendor pattern": "#ea580c",    # orange
        "vendor_pattern": "#ea580c",    # orange (alt spelling)
    }
    tier_display_names = {
        "certain": "TIER 1 · RULES",
        "consistency": "TIER 2 · ML",
        "vendor pattern": "TIER 3 · VENDOR PATTERN",
        "vendor_pattern": "TIER 3 · VENDOR PATTERN",
    }

    for entry in entries:
        # Parse "[tier] message"
        if entry.startswith("[") and "]" in entry:
            tier_raw = entry[1:entry.index("]")].strip().lower()
            message = entry[entry.index("]") + 1:].strip()
        else:
            tier_raw = "unknown"
            message = entry

        color = tier_colors.get(tier_raw, "#6b7280")
        label = tier_display_names.get(tier_raw, tier_raw.upper() or "UNKNOWN")

        st.markdown(
            f'<div style="border-left:3px solid {color};'
            f'padding:6px 12px;margin-bottom:6px;'
            f'background:#1f2937;border-radius:0 6px 6px 0;">'
            f'<span style="color:{color};font-size:11px;font-weight:600;">'
            f'{label}</span><br>'
            f'<span style="color:#d1d5db;font-size:13px;">{message}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_pdf_preview(file_path: str):
    st.markdown("**Original Document**")

    if not file_path:
        st.caption("No file path recorded.")
        return

    clean_path = file_path.lstrip("/")
    candidates = [
        file_path,
        os.path.join(FILES_BASE, os.path.basename(file_path)),
        f"/{clean_path}",
    ]

    found_path = None
    for p in candidates:
        if os.path.exists(p):
            found_path = p
            break

    if not found_path:
        st.warning(f"File not found: `{file_path}`")
        return

    ext = os.path.splitext(found_path)[1].lower()

    if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        try:
            img = Image.open(found_path)
            st.image(img, use_column_width=True)
        except Exception as e:
            st.error(f"Could not open image: {e}")
    elif ext == ".pdf":
        with open(found_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="⬇ Download PDF",
            data=pdf_bytes,
            file_name=os.path.basename(found_path),
            mime="application/pdf",
        )
        st.caption("PDF preview not supported in browser — use the download button above.")
    else:
        st.caption(f"Unsupported file type: {ext}")

def _render_actions(inv, is_flagged: bool, invoice_id: int, on_close, on_refresh):
    st.markdown("**Actions**")

    if is_flagged:
        col1, col2, col3, col4 = st.columns(4)

        # ── 1. Mark Paid (Bloqué si Flagged) ──────────────────────────
        with col1:
            if inv["payment_status"] != "paid":
                if st.button("💳 Mark Paid", key=f"pay_{invoice_id}"):
                    st.error("⚠️ Please correct or approve the invoice before marking it as paid.")
            else:
                st.caption("Already paid.")

        # ── 2. Approve ────────────────────────────────────────────
        with col2:
            if st.button("✅ Approve", key=f"approve_{invoice_id}"):
                approve_invoice(invoice_id)
                st.success("Invoice approved.")
                on_refresh()

        # ── 3. Correct ────────────────────────────────────────────
        with col3:
            if st.button("✏️ Correct", key=f"correct_btn_{invoice_id}"):
                st.session_state[f"show_correct_{invoice_id}"] = True

        # ── 4. Delete ─────────────────────────────────────────────
        with col4:
            if st.button("🗑️ Delete", key=f"delete_{invoice_id}", type="secondary"):
                st.session_state[f"confirm_delete_{invoice_id}"] = True

        # Formulaire de correction
        if st.session_state.get(f"show_correct_{invoice_id}"):
            _render_correction_form(inv, invoice_id, on_refresh)

    else:
        # Factures déjà approuvées ou auto-approuvées
        col1, col2 = st.columns(2)

        with col1:
            if inv["payment_status"] != "paid":
                if st.button("💳 Mark Paid", key=f"pay_{invoice_id}"):
                    mark_paid(invoice_id)
                    st.success("Marked as paid.")
                    on_refresh()
            else:
                st.caption("Already paid.")

        with col2:
            if st.button("🗑️ Delete", key=f"delete_{invoice_id}", type="secondary"):
                st.session_state[f"confirm_delete_{invoice_id}"] = True

    # Confirmation de suppression
    if st.session_state.get(f"confirm_delete_{invoice_id}"):
        st.warning("Are you sure you want to delete this invoice? This cannot be undone.")
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button("Yes, delete", key=f"confirm_yes_{invoice_id}", type="primary"):
                delete_invoice(invoice_id)
                st.success("Invoice deleted.")
                st.session_state[f"confirm_delete_{invoice_id}"] = False
                on_close()
                on_refresh()
        with no_col:
            if st.button("Cancel", key=f"confirm_no_{invoice_id}"):
                st.session_state[f"confirm_delete_{invoice_id}"] = False

def _render_correction_form(inv, invoice_id: int, on_refresh):
    # Charger les line items actuels pour les pré-remplir dans le formulaire
    line_items = fetch_line_items(invoice_id)
    
    with st.form(key=f"correction_form_{invoice_id}"):
        st.markdown("**Correct Invoice Fields**")

        # 1. Édition des métadonnées principales
        new_vendor = st.text_input("Vendor Name", value=inv["vendor_name"] or "")
        new_number = st.text_input("Invoice Number", value=inv["invoice_number"] or "")
        new_date = st.date_input("Invoice Date", value=inv["invoice_date"] if inv["invoice_date"] else None)
        new_currency = st.text_input("Currency (ISO code)", value=inv["currency"] or "", max_chars=3)
        new_amount = st.number_input(
            "Total Amount",
            value=float(inv["total_amount"]) if inv["total_amount"] else 0.0,
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

        # 2. Édition dynamique des articles existants
        st.markdown("---")
        st.markdown("**Correct Line Items**")
        corrected_items = []
        
        if line_items:
            for idx, item in enumerate(line_items):
                st.markdown(f"**Item #{idx + 1}**")
                col_desc, col_qty, col_price = st.columns([3, 1, 1])
                
                desc = col_desc.text_input("Description", value=item["description"] or "", key=f"desc_{invoice_id}_{idx}")
                qty = col_qty.number_input("Qty", value=float(item["quantity"]) if item["quantity"] is not None else 0.0, step=1.0, key=f"qty_{invoice_id}_{idx}")
                price = col_price.number_input("Unit Price", value=float(item["unit_price"]) if item["unit_price"] is not None else 0.0, step=0.01, key=f"price_{invoice_id}_{idx}")
                
                corrected_items.append({
                    "description": desc,
                    "quantity": qty,
                    "unit_price": price
                })
        else:
            st.caption("No items recorded. Correcting headers only.")

        submitted = st.form_submit_button("Save & Approve")
        if submitted:
            correct_invoice(
                invoice_id,
                {
                    "vendor_name":    new_vendor or None,
                    "invoice_number": new_number or None,
                    "invoice_date":   str(new_date) if new_date else None,
                    "currency":       new_currency.upper() or None,
                    "total_amount":   new_amount,
                },
                corrected_items
            )
            st.session_state[f"show_correct_{invoice_id}"] = False
            st.success("Invoice and items corrected and approved.")
            on_refresh()