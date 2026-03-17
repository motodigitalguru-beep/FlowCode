import streamlit as st
import paramiko
from groq import Groq

# 1. Konfiguration & Style
st.set_page_config(page_title="FlowCode Ultimate", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; background-color: #121212; color: #00ff00; }
    div[data-testid="stMetricValue"] { color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Daten laden
groq_key = st.secrets.get("GROQ_API_KEY", "")
ssh_host = st.secrets.get("SSH_HOST", "187.124.28.197")
ssh_user = st.secrets.get("SSH_USER", "root")
ssh_pass = st.secrets.get("SSH_PASS", "")

client = Groq(api_key=groq_key) if groq_key else None

def run_ssh(cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
        # Führt den Befehl in einer Login-Shell aus und unterdrückt Systemfehler
        _, stdout, stderr = ssh.exec_command(f"bash -l -c '{cmd}' 2>/dev/null")
        out, err = stdout.read().decode().strip(), stderr.read().decode().strip()
        ssh.close()
        return out if out else (err if err else "")
    except Exception as e:
        return f"Error: {e}"

# 3. Sidebar
with st.sidebar:
    st.title("🛡️ FlowCode Pro")
    st.info(f"📍 Host: {ssh_host}")
    st.write("---")
    st.subheader("Schnell-Aktionen")
    if st.button("📊 System-Refresh"):
        st.rerun()
    if st.button("🗑️ Chat leeren"):
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    st.caption("KI-Modell: Llama-3.3-70b")

# 4. Dashboard (Status-Karten)
col1, col2, col3 = st.columns(3)

with col1:
    # CPU: Rechnet die Idle-Zeit in Last um
    cpu_raw = run_ssh("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'")
    cpu_val = f"{cpu_raw}%" if cpu_raw else "0%"
    st.metric("CPU Last", cpu_val)

with col2:
    # RAM: Genutzter Speicher in MB
    mem_raw = run_ssh("free -m | awk '/Mem:/ { print $3 }'")
    mem_val = f"{mem_raw} MB" if mem_raw else "0 MB"
    st.metric("RAM (Used)", mem_val)

with col3:
    # Disk: Prozentuale Belegung der Hauptpartition
    disk_raw = run_ssh("df -h / | awk 'NR==2 {print $5}'")
    disk_val = disk_raw if disk_raw else "0%"
    st.metric("Disk Usage", disk_val)

st.write("---")

# 5. Dateieditor
with st.expander("📝 Datei-Quick-Editor (n8n, Configs, etc.)"):
    file_path = st.text_input("Pfad zur Datei (z.B. /root/KI_Test/notiz.txt)", "")
    col_ed1, col_ed2 = st.columns(2)
    
    if col_ed1.button("Datei laden"):
        if file_path:
            content = run_ssh(f"cat {file_path}")
            st.session_state.file_content = content
        else:
            st.warning("Bitte erst einen Pfad eingeben.")
    
    if "file_content" in st.session_state:
        new_content = st.text_area("Inhalt:", value=st.session_state.file_content, height=250)
        if st.button("Änderungen auf Server speichern"):
            # Speichert den Text sicher zurück
            run_ssh(f"echo '{new_content}' > {file_path}")
            st.success("Erfolgreich gespeichert!")

st.write("---")

# 6. Chat Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat-Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Eingabe
if prompt := st.chat_input("Frage mich etwas über deinen Server..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("KI übersetzt Befehl..."):
        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Du bist ein präziser Linux-Terminal. Antworte NUR mit dem Befehl. Keine Erklärungen."},
                    {"role": "user", "content": prompt}
                ]
            )
            cmd = res.choices[0].message.content.strip().replace('```bash', '').replace('```', '').split('\n')[0]
            
            with st.chat_message("assistant"):
                st.code(f"# {cmd}")
                result = run_ssh(cmd)
                if result:
                    st.text_area("Server-Antwort:", value=result, height=200)
                else:
                    st.info("Befehl ausgeführt (keine Rückmeldung).")
                st.session_state.messages.append({"role": "assistant", "content": f"Ausgeführt: `{cmd}`"})
        except Exception as e:
            st.error(f"Fehler: {e}")
