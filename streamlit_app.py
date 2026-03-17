import streamlit as st
import paramiko
from groq import Groq

st.set_page_config(page_title="FlowCode Agent", page_icon="🤖")
st.title("🤖 FlowCode Server Agent (Groq Power)")

with st.sidebar:
    st.header("⚙️ Login")
    ssh_host = st.text_input("Server IP", value="187.124.28.197")
    ssh_user = st.text_input("Benutzer", value="root")
    ssh_pass = st.text_input("SSH Passwort", type="password")
    # Hier kommt dein gsk_... Key rein
    groq_key = st.text_input("Groq API Key", type="password")

if not ssh_pass or not groq_key:
    st.info("Bitte Zugangsdaten in der Sidebar eingeben.")
else:
    client = Groq(api_key=groq_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Befehl an den Server..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Groq denkt nach..."):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Gib NUR den Linux-Befehl aus, keinen Text drumherum."},
                    {"role": "user", "content": prompt}
                ]
            )
            cmd = completion.choices[0].message.content.strip()

        with st.chat_message("assistant"):
            st.code(f"Ausführung: {cmd}")
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if output: st.success(output)
                if error: st.error(error)
                ssh.close()
            except Exception as e:
                st.error(f"SSH Fehler: {e}")
