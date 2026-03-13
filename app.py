import streamlit as st
import paramiko
from openai import OpenAI
import os
from dotenv import load_dotenv

# Lädt die Daten aus deiner .env Datei vom Server
load_dotenv()

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

# Daten-Quelle: Erst .env, dann Streamlit Secrets
ssh_host = os.getenv("SSH_HOST") or st.secrets.get("SSH_HOST")
ssh_user = os.getenv("SSH_USER") or st.secrets.get("SSH_USER")
ssh_pass = os.getenv("SSH_PASS") or st.secrets.get("SSH_PASS")
openai_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
app_pw = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")

# OpenAI Client initialisieren
if openai_key:
    client = OpenAI(api_key=openai_key)

# App Logik
if "authenticated" not in st.session_state:
    eingabe = st.text_input("Admin Passwort", type="password")
    if st.button("Login"):
        if eingabe == app_pw:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Passwort falsch!")
else:
    try:
        ssh = SSHManager(ssh_host, ssh_user, ssh_pass)
        ssh.connect()
        st.success(f"Verbunden mit {ssh_host} 🟢")
        
        wunsch = st.text_input("Was soll ich auf dem Server tun?")
        if wunsch:
            with st.spinner("KI übersetzt..."):
                res = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                              {"role": "user", "content": wunsch}]
                )
                cmd = res.choices[0].message.content.strip()
                st.code(f"Befehl: {cmd}")
                st.text_area("Antwort:", value=ssh.execute_command(cmd))
    except Exception as e:
        st.error(f"Fehler: {e}")
