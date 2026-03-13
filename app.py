import os
from dotenv import load_dotenv
import streamlit as st

# Diese Zeile zwingt das Programm, die .env Datei zu laden
load_dotenv(override=True) 

# Jetzt ziehen wir die Daten sicher raus
ssh_host = os.getenv("SSH_HOST")
openai_key = os.getenv("OPENAI_API_KEY")

# SSH Manager Klasse
class SSHManager:
    def __init__(self, host, user, password):
        self.host, self.user, self.password = host, user, password
        self.client = None
    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, username=self.user, password=self.password, timeout=10)
    def execute_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode()

st.title("🚀 FlowCode Agent")

# Sicherheitscheck: Sind die Secrets da?
if "SSH_HOST" not in st.secrets:
    st.error("Warten auf Secrets... Bitte Seite im Browser neu laden.")
    st.stop()

# Ab hier läuft die App
if "authenticated" not in st.session_state:
    eingabe = st.text_input("Passwort", type="password")
    if st.button("Login"):
        if eingabe == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
else:
    try:
        ssh = SSHManager(st.secrets["SSH_HOST"], st.secrets["SSH_USER"], st.secrets["SSH_PASS"])
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        ssh.connect()
        st.success("Verbunden! 🟢")
        
        user_wunsch = st.text_input("Was soll ich tun?")
        if user_wunsch:
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Nur Linux-Befehl antworten."},
                          {"role": "user", "content": user_wunsch}]
            )
            cmd = res.choices[0].message.content.strip()
            st.code(f"Befehl: {cmd}")
            st.text_area("Antwort:", value=ssh.execute_command(cmd))
    except Exception as e:
        st.error(f"Fehler: {e}")
