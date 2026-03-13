import streamlit as st
import paramiko
from openai import OpenAI

# SSH Manager Klasse direkt im Code
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

# Initialisierung der Clients
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "authenticated" not in st.session_state:
    eingabe = st.text_input("Passwort", type="password")
    if st.button("Login"):
        if eingabe == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
else:
    try:
        ssh = SSHManager(st.secrets["SSH_HOST"], st.secrets["SSH_USER"], st.secrets["SSH_PASS"])
        ssh.connect()
        st.success("Verbunden! 🟢")
        
        user_wunsch = st.text_input("Was soll ich auf dem Server tun?")
        if user_wunsch:
            with st.spinner("KI analysiert..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                              {"role": "user", "content": user_wunsch}]
                )
                cmd = response.choices[0].message.content.strip()
                st.code(f"Befehl: {cmd}")
                st.text_area("Server Antwort:", value=ssh.execute_command(cmd))
    except Exception as e:
        st.error(f"Fehler: {e}")
