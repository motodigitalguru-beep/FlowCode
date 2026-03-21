import streamlit as st
import os
from dotenv import load_dotenv

# ==========================================
# 1. Globale Konfiguration
# ==========================================
st.set_page_config(
    page_title="FlowSystem | B2B Server Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# ==========================================
# 2. Globales "Gedächtnis" (Session States)
# ==========================================
if 'ssh_connected' not in st.session_state:
    st.session_state.ssh_connected = False
if 'server_ip' not in st.session_state:
    st.session_state.server_ip = os.getenv("SSH_HOST", "")
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = [] 

# ==========================================
# 3. Startseite (Willkommens-Screen)
# ==========================================
st.title("🏢 FlowSystem Zentrale")
st.markdown("---")

st.markdown("""
### Willkommen im Control-Center

Dies ist deine skalierbare B2B-Infrastruktur-Lösung. 
Bitte wähle im Menü auf der linken Seite das gewünschte Modul aus:

* **📊 1. Dashboard:** Übersicht über Server-Status und Container.
* **🩺 2. Healthcare:** KI-gestützte Fehleranalyse und Fixes.
* **📦 3. Deployment:** Vollautomatische Erstellung von n8n-Strukturen per Chat.
""")

st.info("👈 Nutze die Sidebar, um zwischen den Modulen zu navigieren.")
