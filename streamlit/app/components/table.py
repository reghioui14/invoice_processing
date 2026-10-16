import streamlit as st
from app.utils.styles import get_status_badge, payment_badge


def render_table(invoices: list, on_select):
    """
    Renders the invoice list as a styled interactive table.
    on_select: callback called when the vendor name is clicked.
    """
    if not invoices:
        st.info("No invoices found in the database yet.")
        return

    # En-têtes de colonnes
    cols = st.columns([0.5, 2.5, 1.5, 1.2, 1.2, 1.8, 1.5])
    headers = ["ID", "Vendor ", "Invoice #", "Date", "Amount", "Status", "Payment"]
    for col, h in zip(cols, headers):
        col.markdown(
            f'<p style="color:#6b7280;font-size:11px;'
            f'text-transform:uppercase;letter-spacing:.06em;margin:0">{h}</p>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="border:none;border-top:1px solid #1f2937;margin:4px 0 8px 0">', unsafe_allow_html=True)

    # Lignes de données — dans une zone scrollable de taille fixe
    with st.container(height=350, border=False):
        for inv in invoices:
            row_cols = st.columns([0.5, 2.5, 1.5, 1.2, 1.2, 1.8, 1.5])

            invoice_date = str(inv["invoice_date"]) if inv["invoice_date"] else "—"
            amount = (
                f"{inv['currency'] or ''} {float(inv['total_amount']):,.2f}"
                if inv["total_amount"] is not None
                else "—"
            )
            validation_str = (inv["validation_reason"] or "").lower()
            status_html = get_status_badge(inv["status"] or "", validation_str)
            pay_html = payment_badge(inv["payment_status"] or "unpaid")

            # 1. ID (Texte simple)
            row_cols[0].markdown(f'<p style="margin:8px 0;color:#9ca3af">{inv["id"]}</p>', unsafe_allow_html=True)

            # 2. Vendeur (Bouton cliquable qui prend toute la colonne)
            vendor_label = f" {inv['vendor_name'] or 'Unknown'}"
            if row_cols[1].button(vendor_label, key=f"sel_{inv['id']}", use_container_width=True):
                on_select(inv["id"])

            # 3. Reste des informations
            row_cols[2].markdown(f'<p style="margin:8px 0;color:#d1d5db">{inv["invoice_number"] or "—"}</p>', unsafe_allow_html=True)
            row_cols[3].markdown(f'<p style="margin:8px 0;color:#d1d5db">{invoice_date}</p>', unsafe_allow_html=True)
            row_cols[4].markdown(f'<p style="margin:8px 0;font-weight:500">{amount}</p>', unsafe_allow_html=True)
            row_cols[5].markdown(f'<div style="margin-top:4px;">{status_html}</div>', unsafe_allow_html=True)
            row_cols[6].markdown(f'<div style="margin-top:6px;">{pay_html}</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border:none;border-top:1px solid #111827;margin:4px 0">', unsafe_allow_html=True)