import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.components.chat import render_chat_history , handle_chat_question
import streamlit as st
from app.db import fetch_all_invoices
from app.utils.styles import GLOBAL_CSS
from app.components.table import render_table
from app.components.detail import render_detail

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invoice Dashboard",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── Session state bootstrap ───────────────────────────────────────────────────
def _init_state():
    if "selected_invoice_id" not in st.session_state:
        st.session_state.selected_invoice_id = None
    if "data_version" not in st.session_state:
        st.session_state.data_version = 0


_init_state()


# ── Callbacks ─────────────────────────────────────────────────────────────────
def select_invoice(invoice_id: int):
    st.session_state.selected_invoice_id = invoice_id
    st.rerun()


def close_detail():
    st.session_state.selected_invoice_id = None
    st.rerun()


def refresh_data():
    st.session_state.data_version += 1
    st.cache_data.clear()
    st.session_state.selected_invoice_id = None
    st.rerun()


# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_invoices(version: int):
    return fetch_all_invoices()


invoices = load_invoices(st.session_state.data_version)


# ── Header épuré (sans bouton refresh) ─────────────────────────────────────────
st.title("🧾 Invoice Dashboard")
st.caption(f"{len(invoices)} invoice(s) in database")


# ── Filter bar ────────────────────────────────────────────────────────────────
with st.expander("🔍 Filters", expanded=False):
    f1, f2, f3 = st.columns(3)

    all_statuses = ["All", "auto_approved", "approved", "flagged"]
    status_filter = f1.selectbox("Status", all_statuses)

    all_payments = ["All", "paid", "unpaid"]
    payment_filter = f2.selectbox("Payment", all_payments)

    search_vendor = f3.text_input("Vendor name contains", "")

# Apply filters
filtered = invoices
if status_filter != "All":
    filtered = [i for i in filtered if (i["status"] or "").strip().lower() == status_filter.lower()]
if payment_filter != "All":
    filtered = [i for i in filtered if (i["payment_status"] or "unpaid").strip().lower() == payment_filter.lower()]
if search_vendor:
    filtered = [
        i for i in filtered
        if search_vendor.lower() in (i["vendor_name"] or "").lower()
    ]
# ── Layout : détail en pleine largeur, sinon Dashboard à gauche / Chat à droite ──
if st.session_state.selected_invoice_id is not None:
    render_detail(
        invoice_id=st.session_state.selected_invoice_id,
        on_close=close_detail,
        on_refresh=refresh_data,
    )
else:
    col_dashboard, col_chat = st.columns([2, 1])
    with col_dashboard:
        render_table(filtered, on_select=select_invoice)
    with col_chat:
        render_chat_history()

# chat_input appelé HORS des colonnes, à la racine → reste épinglé en bas
question = st.chat_input("Ask something, e.g. 'Which vendor has the highest total amount?'")
if question:
    handle_chat_question(question)# ── Layout : détail en pleine largeur, sinon Dashboard à gauche / Chat à droite ──
