import streamlit as st
from ssh_client import SSHManager
from openai import OpenAI

st.title("🚀 FlowCode Admin")

# 1. Prüfen ob Secrets da sind
if "APP_PASSWORD" not in st.secrets:
    st.error("Fehler: APP_PASSWORD wurde in den Secrets nicht gefunden!")
else:
    # 2. Passwort-Abfrage
    if "auth" not in st.session_state:
        pw = st.text_input("Admin-Passwort", type="password")
        if pw == st.secrets["APP_PASSWORD"]:
            st.session_state["auth"] = True
            st.rerun()
    else:
        # 3. Wenn eingeloggt, zeige die App
        try:
            ssh = SSHManager(st.secrets["SSH_HOST"], st.secrets["SSH_USER"], st.secrets["SSH_PASS"])
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
            ssh.connect()
            st.success("Verbunden mit Server 🟢")
            
            frage = st.text_input("Was soll ich tun?")
            if frage:
                with st.spinner("KI denkt nach..."):
                    res = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                                  {"role": "user", "content": frage}]
                    )
                    cmd = res.choices[0].message.content.strip()
                    st.code(f"Befehl: {cmd}")
                    out = ssh.execute_command(cmd)
                    st.text_area("Server-Antwort:", value=out, height=200)
                    
        except Exception as e:
            st.error(f"Verbindung fehlgeschlagen: {e}")
