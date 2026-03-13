import streamlit as st
import os
from ssh_client import SSHManager
from openai import OpenAI

# 1. Passwort-Schutz Logik
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
    elif not st.session_state["password_correct"]:
        st.text_input("Bitte Admin-Passwort eingeben", type="password", on_change=password_entered, key="password")
        st.error("😕 Passwort falsch.")
        return False
    return True

# 2. Wenn Passwort korrekt, zeige App
if check_password():
    # Daten aus Secrets laden
    ssh_host = st.secrets["SSH_HOST"]
    ssh_user = st.secrets["SSH_USER"]
    ssh_pass = st.secrets["SSH_PASS"]
    api_key = st.secrets["OPENAI_API_KEY"]

    client = OpenAI(api_key=api_key)
    ssh = SSHManager(ssh_host, ssh_user, ssh_pass)

    st.title("🚀 FlowCode | Admin-Dashboard")

    try:
        ssh.connect()
        st.success("Server Status: Online 🟢")
        
        # WICHTIG: Hier heißt die Variable jetzt 'user_query'
        user_query = st.text_input("KI-Agent: Welchen Befehl soll ich ausführen?")
        
        if user_query:
            with st.spinner("KI denkt nach..."):
                # Die KI entscheidet, welcher Befehl nötig ist
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Du bist ein Linux-Experte. Antworte NUR mit dem exakten Bash-Befehl, ohne Text drumherum."},
                        {"role": "user", "content": user_query}
                    ]
                )
                linux_command = response.choices[0].message.content.strip()
                
                # Befehl anzeigen und ausführen
                st.code(f"Ausführung: {linux_command}", language="bash")
                result = ssh.execute_command(linux_command)
                st.text_area("Server Antwort:", value=result, height=300)
                
    except Exception as e:
        st.error(f"Fehler: {e}")
