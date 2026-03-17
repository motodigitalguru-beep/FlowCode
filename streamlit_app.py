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
    div[data-testid="stMetricValue"] { color: white !important; font-size: 1.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Daten laden aus Secrets
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
        # Nutzt bash -c und leitet Fehler um, um nur saubere Daten zu erhalten
        _, stdout, stderr = ssh.exec_command(f"bash -c \"{cmd}\" 2>/dev/null")
        out = stdout.read().decode().strip()
        ssh.close()
        return out
    except Exception as e:
        return ""

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

# 4. Dashboard (Status-Karten) - Jetzt absolut sauber
col1, col2, col3 = st.columns(3)

with col1:
    # CPU: Bleibt wie sie ist, da sie auf Bild 20 bereits funktioniert (0%)
    cpu_val = run_ssh("top -bn1 | grep 'Cpu(s)' | awk '{print 100 - $8}'")
    st.metric("CPU Last", f"{cpu_val}%" if cpu_val else "0%")

with col2:
    # RAM: Wir nehmen nur den ersten Wert (Used)
    # Filtert alles außer der reinen Zahl für den verbrauchten RAM heraus
    mem_val = run_ssh("free -m | awk '/Mem:/ { print $3 }' | head -n 1")
    st.metric("RAM (Used)", f"{mem_val} MB" if mem_val else "0 MB")

with col3:
    # Disk: Wir nehmen nur die Prozentzahl (z.B. 10%)
    # Nutzt awk, um nur die Spalte mit der Prozentangabe auszugeben
    disk_val = run_ssh("df -h / | awk 'NR==2 {print $5}' | head -n 1")
    st.metric("Disk Usage", disk_val if disk_val else "0%")
    
st.write("---")

# 5. Dateieditor
with st.expander("📝 Datei-Quick-Editor (n8n, Configs, etc.)"):
    f_path = st.text_input("Pfad zur Datei:", "/root/KI_Test/notiz.txt")
    if st.button("Datei laden"):
        st.session_state.file_content = run_ssh(f"cat {f_path}")
        st.session_state.current_path = f_path
    
    if "file_content" in st.session_state:
        edited = st.text_area("Inhalt:", value=st.session_state.file_content, height=250)
        if st.button("Speichern"):
            # Speichert den Text per Echo-Befehl
            save_cmd = f"echo '{edited}' > {st.session_state.current_path}"
            run_ssh(save_cmd)
            st.success("Gespeichert!")

# 6. Chat Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage mich etwas über deinen Server..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("KI übersetzt..."):
        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Antworte NUR mit dem Linux-Befehl. Keine Erklärungen."},
                    {"role": "user", "content": prompt}
                ]
            )
            cmd = res.choices[0].message.content.strip().replace('```bash', '').replace('```', '').split('\n')[0]
            
            with st.chat_message("assistant"):
                st.code(f"# {cmd}")
                result = run_ssh(cmd)
                if result:
                    st.text_area("Ergebnis:", value=result, height=200)
                else:
                    st.info("Ausgeführt.")
                st.session_state.messages.append({"role": "assistant", "content": f"Befehl: `{cmd}`"})
        except Exception as e:
            st.error(f"Fehler: {e}")
