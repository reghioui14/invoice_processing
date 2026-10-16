import streamlit as st
import requests
import os

N8N_CHAT_WEBHOOK = os.getenv(
    "N8N_CHAT_WEBHOOK",
    "http://n8n:5678/webhook/invoice-chat"
)

def render_chat_history():
    st.markdown("### 💬 Ask me ")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.container(height=300, border=True):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

def handle_chat_question(question):
    st.session_state.chat_history.append({"role": "user", "content": question})
    try:
        response = requests.post(N8N_CHAT_WEBHOOK, json={"question": question}, timeout=120)
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer") or data.get("output", "No answer returned.")
    except Exception as e:
        answer = f"⚠️ Error contacting the AI agent: {e}"
    st.session_state.chat_history.append({"role": "assistant", "content": answer})
    st.rerun()