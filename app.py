import streamlit as st
import os
from dotenv import load_dotenv
from ssh_client import SSHManager

# 1. Versuche erst die Cloud-Secrets, dann die lokale .env
if "SSH_HOST" in st.secrets:
    # Wir sind in der Cloud
    ssh_host = st.secrets["SSH_HOST"]
    ssh_user = st.secrets["SSH_USER"]
    ssh_pass = st.secrets["SSH_PASS"]
    # Falls du OpenAI nutzt:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    # Wir sind lokal auf deinem Mac
    load_dotenv()
    ssh_host = os.getenv("SSH_HOST")
    ssh_user = os.getenv("SSH_USER")
    ssh_pass = os.getenv("SSH_PASS")

ssh = SSHManager(ssh_host, ssh_user, ssh_pass)

# Hauptbereich
st.title("🚀 FlowCode Agent")
st.subheader("Dein intelligenter n8n & Docker Admin")

# Status-Check (Ampel)
try:
    ssh.connect()
    st.success(f"🟢 Verbunden mit {h}")
    ssh.close()
except:
    st.error("🔴 Verbindung fehlgeschlagen. Prüfe deine Daten in der Sidebar.")

# KI-Eingabe
if 'history' not in st.session_state:
    st.session_state.history = []

user_wunsch = st.text_input("Was soll ich auf dem Server erledigen?", placeholder="z.B. Prüfe ob n8n läuft")

if user_wunsch:
    with st.spinner("KI analysiert..."):
        prompt = f"User will: {user_wunsch}. Erkläre kurz auf Deutsch, was du tust, und gib dann den Linux-Befehl aus. Trenne beides mit einem '|'. Format: Erklärung | Befehl"
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        ki_res = response.choices[0].message.content
        
        parts = ki_res.split("|")
        erlaeuterung = parts[0].strip()
        befehl = parts[1].strip() if len(parts) > 1 else ""

        st.warning(f"**Plan:** {erlaeuterung}")
        if befehl:
            st.code(befehl, language="bash")
            if st.button("Befehl jetzt ausführen"):
                ssh.connect()
                output = ssh.execute(befehl)
                st.session_state.history.append({"cmd": befehl, "res": output})
                st.success("Erledigt!")
                st.code(output)
                ssh.close()

# Verlauf
if st.session_state.history:
    st.divider()
    st.write("### 🕒 Verlauf")
    for item in reversed(st.session_state.history):
        with st.expander(f"Befehl: {item['cmd']}"):
            st.code(item['res'])
