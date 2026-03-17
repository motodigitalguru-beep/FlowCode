import streamlit as st
import paramiko
from groq import Groq
import io
from PIL import Image

# 1. Konfiguration & Style
st.set_page_config(page_title="FlowCode Factory", page_icon="🎨", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    div[data-testid="stMetricValue"] { color: #00ff00 !important; }
    .stSelectbox div[data-baseweb="select"] { color: white; background-color: #121212; border-color: #333; }
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
        # Nutzt bash -c und leitet Fehler um, um nur saubere Daten zu erhalten
        _, stdout, stderr = ssh.exec_command(f"bash -c \"{cmd}\" 2>/dev/null")
        out = stdout.read().decode().strip()
        ssh.close()
        return out
    except: return ""

# 3. Sidebar
with st.sidebar:
    st.title("🛡️ FlowCode Pro")
    st.caption("v2.8 - Media Edition")
    if st.button("🔄 Refresh"): st.rerun()
    if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

# 4. Dashboard (CPU/RAM/Disk)
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

# 5. KORRIGIERT: Robusterer Media Viewerst.write("---")

# 5. VERBESSERT: Robuste Media Gallery & Viewer
with st.expander("🖼️ Clawbot Image Galerie (Verbessert)", expanded=True):
    # Nutzen find statt ls, da find toleranter ist (case-insensitive)
    # Sucht PNG, JPG, JPEG, egal ob groß oder klein geschrieben
    img_list_raw = run_ssh("find /root/clawbot/images -maxdepth 1 -type f \\( -iname \"*.png\" -o -iname \"*.jpg\" -o -iname \"*.jpeg\" \\) 2>/dev/null")
    
    if img_list_raw:
        # Erstellt die Liste und filtert leere Zeilen
        img_list = [f for f in img_list_raw.split('\n') if f.strip()]
        selected_img = st.selectbox("Wähle ein Bild aus:", img_list)
        
        if st.button("Bild laden & anzeigen"):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                sftp = ssh.open_sftp()
                
                # Datei binär vom Server lesen
                with sftp.open(selected_img, 'rb') as f:
                    img_data = f.read()
                
                sftp.close()
                ssh.close()
                
                # Bild im Speicher in Pillow konvertieren
                image = Image.open(io.BytesIO(img_data))
                st.image(image, caption=f"Vorschau: {selected_img}", use_container_width=True)
            except Exception as e:
                st.error(f"Fehler beim Laden des Bildes: {e}")
    else:
        st.info("Keine Bilder (.png, .jpg) im Ordner /root/clawbot/images gefunden. Prüfe die Pfade.")

st.write("---")

# 6. Dateieditor
with st.expander("📝 Config Editor"):
    f_path = st.text_input("Pfad zur Datei:", "/root/clawbot/flux_workflow.json")
    ed_col1, ed_col2 = st.columns(2)
    
    if ed_col1.button("📂 Laden"):
        st.session_state.file_content = run_ssh(f"cat {f_path}")
        st.session_state.current_path = f_path
        st.success(f"Geladen: {f_path}")
    
    if "file_content" in st.session_state:
        edited = st.text_area("Inhalt:", value=st.session_state.file_content, height=200)
        if st.button("💾 Speichern"):
            # Speichert den Text per Echo-Befehl
            save_cmd = f"echo '{edited}' > {st.session_state.current_path}"
            run_ssh(save_cmd)
            st.success("Änderungen gespeichert!")

st.write("---")

# 7. AI Agent Chat
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if pr := st.chat_input("Server-Befehl senden..."):
    st.session_state.messages.append({"role": "user", "content": pr})
    with st.chat_message("user"): st.markdown(pr)
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":"Antworte NUR mit dem Linux-Befehl. Keine Erklärungen."},{"role":"user","content":pr}]
    )
    cmd = res.choices[0].message.content.strip().replace('```', '').split('\n')[0]
    with st.chat_message("assistant"):
        st.code(f"# {cmd}")
        out = run_ssh(cmd)
        if out: st.text_area("Ausgabe:", value=out, height=150)
        else: st.info("Befehl ohne Rückmeldung ausgeführt.")
        st.session_state.messages.append({"role": "assistant", "content": f"Befehl: `{cmd}`"})
