import streamlit as st
import paramiko
from groq import Groq

# 1. Page Config & Professional UI
st.set_page_config(page_title="FlowCode Ultimate", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; }
    div[data-testid="stMetricValue"] { color: #00ff00 !important; font-size: 2rem !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #999 !important; }
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; background-color: #000; color: #00ff00; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. Secrets & Credentials
groq_key = st.secrets.get("GROQ_API_KEY", "")
ssh_host = st.secrets.get("SSH_HOST", "187.124.28.197")
ssh_user = st.secrets.get("SSH_USER", "root")
ssh_pass = st.secrets.get("SSH_PASS", "")

client = Groq(api_key=groq_key) if groq_key else None

def run_ssh(cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_user, password=ssh_pass, timeout=5)
        # Wir nutzen /bin/bash explizit und leiten ALLE Fehler nach /dev/null um
        _, stdout, stderr = ssh.exec_command(f"/bin/bash -c \"{cmd}\" 2>/dev/null")
        out = stdout.read().decode().strip()
        ssh.close()
        return out if out else ""
    except:
        return ""

# 3. Sidebar mit Control Panel
with st.sidebar:
    st.title("🛡️ FlowCode Pro")
    st.info(f"🌐 Host: {ssh_host}")
    st.write("---")
    if st.button("🔄 System-Refresh"):
        st.rerun()
    if st.button("🗑️ Chat leeren"):
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    st.caption("v2.5 Professional Edition")

# 4. Clean Dashboard Metrics
col1, col2, col3 = st.columns(3)

with col1:
    # CPU: Nutzt 'top' im Batch-Mode, isoliert nur die IDLE-Zahl und rechnet (100 - idle)
    cpu = run_ssh("top -bn1 | grep 'Cpu(s)' | awk '{print $8}' | cut -d',' -f1 | cut -d'.' -f1")
    cpu_display = f"{100 - int(cpu)}%" if cpu and cpu.isdigit() else "0%"
    st.metric("CPU Auslastung", cpu_display)

with col2:
    # RAM: Nimmt nur den genutzten Wert aus 'free -m'
    ram = run_ssh("free -m | awk '/Mem:/ {print $3}'")
    st.metric("RAM (Used)", f"{ram} MB" if ram else "N/A")

with col3:
    # Disk: Nimmt nur den Prozentwert der Hauptpartition
    disk = run_ssh("df -h / | awk 'NR==2 {print $5}'")
    st.metric("Disk Usage", disk if disk else "N/A")

st.write("---")

# 5. File Quick-Editor
with st.expander("📝 Datei-Editor (Configs & n8n)"):
    f_path = st.text_input("Pfad zur Datei:", "/root/KI_Test/notiz.txt")
    ed_col1, ed_col2 = st.columns(2)
    
    if ed_col1.button("📂 Datei laden"):
        st.session_state.file_content = run_ssh(f"cat {f_path}")
        st.session_state.current_path = f_path
        st.success(f"Geladen: {f_path}")
    
    if "file_content" in st.session_state:
        edited = st.text_area("Inhalt:", value=st.session_state.file_content, height=200)
        if st.button("💾 Speichern"):
            # Speichert den Text per Echo-Befehl
            run_ssh(f"echo '{edited}' > {st.session_state.current_path}")
            st.success("Änderungen gespeichert!")

# 6. AI Agent Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Server-Kommando senden..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Agent übersetzt..."):
        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Antworte NUR mit dem Linux-Befehl. Keine Erklärungen."},
                    {"role": "user", "content": prompt}
                ]
            )
            cmd = res.choices[0].message.content.strip().replace('```', '').split('\n')[0]
            
            with st.chat_message("assistant"):
                st.code(f"# {cmd}")
                result = run_ssh(cmd)
                if result:
                    st.text_area("Ausgabe:", value=result, height=200)
                else:
                    st.info("Befehl ohne Rückmeldung ausgeführt.")
                st.session_state.messages.append({"role": "assistant", "content": f"Befehl: `{cmd}`"})
        except Exception as e:
            st.error(f"Fehler: {e}")
