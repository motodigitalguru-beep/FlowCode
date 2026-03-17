import streamlit as st
import paramiko
from groq import Groq

# 1. Page Styling & Header
st.set_page_config(page_title="FlowCode Pro Terminal", page_icon="⚡", layout="wide")

# Custom CSS für einen professionellen Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; }
    .stButton>button:hover { background-color: #ff4b4b; border-color: #ff4b4b; }
    .status-box { padding: 20px; border-radius: 10px; background-color: #1e1e1e; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. Daten laden
groq_key = st.secrets.get("GROQ_API_KEY", "")
ssh_host = st.secrets.get("SSH_HOST", "187.124.28.197")
ssh_user = st.secrets.get("SSH_USER", "root")
ssh_pass = st.secrets.get("SSH_PASS", "")

client = Groq(api_key=groq_key) if groq_key else None

# 3. Sidebar mit Schnell-Befehlen
with st.sidebar:
    st.title("⚡ Control Center")
    st.markdown(f"**Host:** `{ssh_host}`")
    st.markdown(f"**User:** `{ssh_user}`")
    st.success("Connected" if ssh_pass else "Missing Credentials")
    
    st.write("---")
    st.subheader("Quick Actions")
    quick_top = st.button("📊 CPU & Prozesse")
    quick_df = st.button("💾 Speicherplatz")
    quick_ls = st.button("📂 Verzeichnis-Check")
    
    if st.button("🗑️ Chat löschen"):
        st.session_state.messages = []
        st.rerun()

# 4. Chat Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header Anzeige
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🚀 FlowCode Server Agent")
    st.caption("Admin-Interface gesteuert durch Llama 3.3")

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Funktion zur Befehlsausführung
def execute_cmd(user_prompt):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.spinner("AI thinking..."):
        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl. Hänge ' 2>/dev/null' an."},
                          {"role": "user", "content": user_prompt}]
            )
            cmd = res.choices[0].message.content.strip().split('\n')[0].replace('```', '').strip()
            
            with st.chat_message("assistant"):
                st.code(f"EXEC: {cmd}")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                _, stdout, stderr = ssh.exec_command(f"bash -l -c '{cmd}'")
                out, err = stdout.read().decode(), stderr.read().decode()
                
                response = out if out else (err if err else "Done.")
                st.text_area("Result:", value=response, height=200)
                st.session_state.messages.append({"role": "assistant", "content": f"Befehl ausgeführt: `{cmd}`"})
                ssh.close()
        except Exception as e:
            st.error(f"Error: {e}")

# Eingabe verarbeiten
if prompt := st.chat_input("Befehl eingeben..."):
    execute_cmd(prompt)

# Quick Buttons verarbeiten
if quick_top: execute_cmd("Zeig mir die CPU Auslastung")
if quick_df: execute_cmd("Zeig mir den freien Speicherplatz")
if quick_ls: execute_cmd("Liste alle Dateien im aktuellen Ordner auf")
