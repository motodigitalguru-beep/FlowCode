import streamlit as st
from ssh_client import SSHManager
from openai import OpenAI

st.title("🚀 FlowCode Admin")

# Hier prüfen wir, ob die Namen aus deinen Secrets EXAKT so existieren
required = ["85.215.155.197", "root", "Mephisto10.11,1975?", "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", "FlowCode2024"]
vorhanden = [k for k in required if k in st.secrets]

if len(vorhanden) < len(required):
    st.error(f"Folgende Keys fehlen noch: {set(required) - set(vorhanden)}")
    st.write("Vorhanden sind:", vorhanden)
else:
    # Login Bereich
    if "authenticated" not in st.session_state:
        eingabe = st.text_input("Passwort", type="password")
        if eingabe == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
    else:
        # App Bereich
        try:
            ssh = SSHManager(st.secrets["SSH_HOST"], st.secrets["SSH_USER"], st.secrets["SSH_PASS"])
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            ssh.connect()
            st.success("Verbunden! 🟢")
            
            abfrage = st.text_input("Was soll ich tun?")
            if abfrage:
                res = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "Antworte nur mit dem Linux-Befehl."},
                              {"role": "user", "content": abfrage}]
                )
                cmd = res.choices[0].message.content.strip()
                st.code(f"Befehl: {cmd}")
                st.text_area("Server Antwort:", value=ssh.execute_command(cmd))
        except Exception as e:
            st.error(f"Fehler: {e}")
