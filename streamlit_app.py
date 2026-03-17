import streamlit as st
import paramiko
from groq import Groq
import io
from PIL import Image

# 1. Konfiguration
st.set_page_config(page_title="FlowCode Factory", page_icon="🎨", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    div[data-testid="stMetricValue"] { color: #00ff00 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Credentials
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
        _, stdout, stderr = ssh.exec_command(f"bash -c \"{cmd}\" 2>/dev/null")
        out = stdout.read().decode().strip()
        ssh.close()
        return out
    except: return ""

# 3. Sidebar
with st.sidebar:
    st.title("🛡️ FlowCode Pro")
    if st.button("🔄 Refresh"): st.rerun()
    if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

# 4. Dashboard
col1, col2, col3 = st.columns(3)
with col1:
    cpu = run_ssh("top -bn1 | grep 'Cpu(s)' | awk '{print $8}' | cut -d',' -f1 | cut -d'.' -f1")
    st.metric("CPU Last", f"{100 - int(cpu)}%" if cpu and cpu.isdigit() else "0%")
with col2:
    ram = run_ssh("free -m | awk '/Mem:/ {print $3}'")
    st.metric("RAM (Used)", f"{ram} MB" if ram else "N/A")
with col3:
    disk = run_ssh("df -h / | awk 'NR==2 {print $5}'")
    st.metric("Disk Usage", disk if disk else "N/A")

st.write("---")

# 5. NEU: Media Gallery & Viewer
with st.expander("🖼️ Clawbot Image Gallery", expanded=True):
    # Liste der Bilder abrufen
    img_list_raw = run_ssh("ls /root/clawbot/images/*.png /root/clawbot/images/*.jpg")
    if img_list_raw:
        img_list = img_list_raw.split('\n')
        selected_img = st.selectbox("Wähle ein Bild aus:", img_list)
        
        if st.button("Bild anzeigen"):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                sftp = ssh.open_sftp()
                with sftp.open(selected_img, 'rb') as f:
                    img_data = f.read()
                sftp.close()
                ssh.close()
                
                image = Image.open(io.BytesIO(img_data))
                st.image(image, caption=f"Vorschau: {selected_img}", use_container_width=True)
            except Exception as e:
                st.error(f"Fehler beim Laden des Bildes: {e}")
    else:
        st.info("Keine Bilder im Ordner /root/clawbot/images gefunden.")

st.write("---")

# 6. Dateieditor
with st.expander("📝 Config Editor"):
    f_path = st.text_input("Pfad:", "/root/clawbot/flux_workflow.json")
    if st.button("Laden"):
        st.session_state.file_content = run_ssh(f"cat {f_path}")
        st.session_state.current_path = f_path
    if "file_content" in st.session_state:
        edited = st.text_area("Inhalt:", value=st.session_state.file_content, height=200)
        if st.button("Speichern"):
            run_ssh(f"echo '{edited}' > {st.session_state.current_path}")
            st.success("Gespeichert!")

# 7. Chat
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if pr := st.chat_input("Befehl..."):
    st.session_state.messages.append({"role": "user", "content": pr})
    with st.chat_message("user"): st.markdown(pr)
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":"NUR Linux-Befehl antworten."},{"role":"user","content":pr}]
    )
    cmd = res.choices[0].message.content.strip().replace('```', '').split('\n')[0]
    with st.chat_message("assistant"):
        st.code(f"# {cmd}")
        out = run_ssh(cmd)
        if out: st.text_area("Ausgabe:", value=out, height=150)
        else: st.info("Erledigt.")
        st.session_state.messages.append({"role": "assistant", "content": f"Befehl: `{cmd}`"})
