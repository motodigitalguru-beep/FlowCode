import streamlit as st
import paramiko
from groq import Groq

st.set_page_config(page_title="FlowCode Agent", page_icon="🤖")
st.title("🤖 FlowCode Server Agent")

# 1. Daten aus den Secrets laden
# Wir versuchen die Daten aus den Secrets zu ziehen. 
# Falls sie nicht da sind, bleiben die Variablen leer.
groq_key = st.secrets.get("GROQ_API_KEY", "")
ssh_host = st.secrets.get("SSH_HOST", "187.124.28.197")
ssh_user = st.secrets.get("SSH_USER", "root")
ssh_pass = st.secrets.get("SSH_PASS", "")

# 2. Client Initialisierung
client = None
if groq_key:
    client = Groq(api_key=groq_key)

# Chat-Historie im Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Eingabe-Logik
if prompt := st.chat_input("Was soll ich auf dem Server tun?"):
    # Prüfung: Sind alle Daten da (entweder aus Secrets oder Sidebar)?
    if not groq_key or not ssh_pass:
        st.error("❌ Fehler: Keys oder SSH-Passwort fehlen in den Streamlit Secrets!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Groq denkt nach..."):
            try:
                # Hier nutzen wir das AKTUELLSTE Modell
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                        {"role": "user", "content": prompt}
                    ]
                )
                cmd = res.choices[0].message.content.strip().replace('```bash', '').replace('```', '')

                with st.chat_message("assistant"):
                    st.info(f"Führe aus: `{cmd}`")
                    
                    # SSH Verbindung
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                    
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    out = stdout.read().decode()
                    err = stderr.read().decode()
                    
                    if out: st.code(out)
                    if err: st.error(err)
                    ssh.close()
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
