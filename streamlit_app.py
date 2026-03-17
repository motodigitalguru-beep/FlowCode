import streamlit as st
import paramiko
from groq import Groq

st.set_page_config(page_title="FlowCode Agent", page_icon="🤖")
st.title("🤖 FlowCode Server Agent")

# Sidebar für Login-Daten
with st.sidebar:
    st.header("⚙️ Login")
    ssh_host = st.text_input("Server IP", value="187.124.28.197")
    ssh_user = st.text_input("Benutzer", value="root")
    ssh_pass = st.text_input("SSH Passwort", type="password")
    groq_key = st.text_input("Groq API Key", type="password")

# --- WICHTIG: Client sicher initialisieren ---
client = None
if groq_key:
    client = Groq(api_key=groq_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat-Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Eingabe-Logik
if prompt := st.chat_input("Befehl an den Server..."):
    if not client or not ssh_pass:
        st.error("Bitte zuerst SSH-Passwort und Groq-Key in der Sidebar eingeben!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Groq denkt nach..."):
            try:
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Gib NUR den Linux-Befehl aus, keinen Text."},
                        {"role": "user", "content": prompt}
                    ]
                )
                cmd = completion.choices[0].message.content.strip()

                with st.chat_message("assistant"):
                    st.info(f"Führe aus: {cmd}")
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                    
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    out, err = stdout.read().decode(), stderr.read().decode()
                    
                    if out: st.success(out)
                    if err: st.error(err)
                    ssh.close()
            except Exception as e:
                st.error(f"Fehler: {e}")
