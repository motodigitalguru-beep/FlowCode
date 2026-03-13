import streamlit as st
import os
from ssh_client import SSHManager
from openai import OpenAI

# 1. Passwort-Schutz
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("Bitte Admin-Passwort eingeben", type="password", on_change=password_entered, key="password")
        return False
    return True

if check_password():
    # Daten aus Secrets
    ssh_host = st.secrets["SSH_HOST"]
    ssh_user = st.secrets["SSH_USER"]
    ssh_pass = st.secrets["SSH_PASS"]
    api_key = st.secrets["OPENAI_API_KEY"]

    client = OpenAI(api_key=api_key)
    ssh = SSHManager(ssh_host, ssh_user, ssh_pass)

    st.title("🚀 FlowCode | KI-Admin")

    try:
        ssh.connect()
        st.success("Server Status: Online 🟢")
        
        user_input = st.text_input("Was soll ich auf dem Server tun?", placeholder="z.B. Zeig mir alle Dateien oder CPU Last")
        
        if user_input:
            with st.spinner("KI denkt nach..."):
                # KI entscheidet, welcher Linux-Befehl nötig ist
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Du bist ein Server-Experte. Antworte NUR mit dem passenden Linux-Befehl, ohne Text drumherum."},
                        {"role": "user", "content": user_input}
                    ]
                )
                linux_command = response.choices[0].message.content.strip()
                
                st.code(f"Ausführung: {linux_command}", language="bash")
                
                # Befehl auf Server ausführen
                result = ssh.execute_command(linux_command)
                st.text_area("Server Ergebnis:", value=result, height=200)
                
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
