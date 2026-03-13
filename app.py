import streamlit as st
import os
from ssh_client import SSHManager
from openai import OpenAI

# 1. Passwort-Schutz
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Bitte Admin-Passwort eingeben", type="password", key="password_input")
        if st.session_state.password_input == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if check_password():
    # Verbindung herstellen
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    ssh = SSHManager(st.secrets["SSH_HOST"], st.secrets["SSH_USER"], st.secrets["SSH_PASS"])

    st.title("🚀 FlowCode Admin")

    try:
        ssh.connect()
        st.success("Verbunden! 🟢")
        
        # HIER IST DIE WICHTIGE STELLE:
        befehl_text = st.text_input("Was soll ich tun?")
        
        if befehl_text:
            with st.spinner("KI arbeitet..."):
                # KI nach dem Linux-Befehl fragen
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                        {"role": "user", "content": befehl_text}
                    ]
                )
                kommando = response.choices[0].message.content.strip()
                
                st.code(f"Befehl: {kommando}")
                ergebnis = ssh.execute_command(kommando)
                st.text_area("Antwort vom Server:", value=ergebnis, height=200)
                
    except Exception as e:
        st.error(f"Fehler: {e}")
