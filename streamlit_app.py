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
        _, stdout, stderr = ssh.exec_command(f"bash -l -c '{cmd} 2>/dev/null'")
        out, err = stdout.read().decode(), stderr.read().decode()
        ssh.close()
        return out if out else err
    except Exception as e:
        return f"Error: {e}"

# 3. Sidebar
with st.sidebar:
    st.title("🛡️ FlowCode Pro")
    st.info(f"📍 {ssh_host}")
    st.write("---")
    st.subheader("Schnell-Aktionen")
    if st.button("📊 System-Refresh"):
        st.rerun()
    if st.button("🗑️ Chat leeren"):
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    st.caption("Modell: Llama-3.3-70b")

# 4. Dashboard (Status-Karten)
col1, col2, col3 = st.columns(3)
with col1:
    cpu_info = run_ssh("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
    st.metric("CPU Last", f"{cpu_info.strip()}%")
with col2:
    mem_info = run_ssh("free -m | awk '/Mem:/ { print $3 }'")
    st.metric("RAM (Used)", f"{mem_info.strip()} MB")
with col3:
    disk_info = run_ssh("df -h / | awk '/\\// {print $5}'")
    st.metric("Disk Usage", disk_info.strip())

st.write("---")

# 5. Dateieditor (Neu!)
with st.expander("📝 Datei-Quick-Editor"):
    file_path = st.text_input("Pfad zur Datei (z.B. /root/index.html)", "")
    if st.button("Datei laden"):
        content = run_ssh(f"cat {file_path}")
        st.session_state.file_content = content
    
    if "file_content" in st.session_state:
        new_content = st.text_area("Inhalt bearbeiten:", value=st.session_state.file_content, height=300)
        if st.button("Datei auf Server speichern"):
            # Speichert den Inhalt sicher zurück
            run_ssh(f"echo '{new_content}' > {file_path}")
            st.success(f"Datei {file_path} wurde aktualisiert!")

st.write("---")

# 6. Chat Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Befehl oder Frage an den Server..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("AI verarbeitet..."):
        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                          {"role": "user", "content": prompt}]
            )
            cmd = res.choices[0].message.content.strip().split('\n')[0].replace('```', '').strip()
            
            with st.chat_message("assistant"):
                st.code(cmd)
                result = run_ssh(cmd)
                st.text_area("Antwort:", value=result if result else "Befehl ausgeführt.", height=150)
                st.session_state.messages.append({"role": "assistant", "content": f"Befehl: `{cmd}`"})
        except Exception as e:
            st.error(f"Fehler: {e}")
