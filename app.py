import streamlit as st
import paramiko
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

st.title("🚀 FlowCode Agent")

# Daten laden
ssh_host = os.getenv("SSH_HOST") or st.secrets.get("SSH_HOST")
ssh_user = os.getenv("SSH_USER") or st.secrets.get("SSH_USER")
ssh_pass = os.getenv("SSH_PASS") or st.secrets.get("SSH_PASS")
openai_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

app_pw = st.secrets.get("APP_PASSWORD", "FlowCode2024")

# OpenAI Client
client = None
if openai_key:
    client = OpenAI(api_key=openai_key)
else:
    st.error("OpenAI Key fehlt!")

# Login
if "auth" not in st.session_state:
    eingabe = st.text_input("Passwort", type="password")

    if st.button("Login"):
        if eingabe == app_pw:
            st.session_state["auth"] = True
            st.rerun()

else:

    if client:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                ssh_host,
                username=ssh_user,
                password=ssh_pass,
                timeout=10
            )

            st.success(f"Verbunden mit {ssh_host}")

            wunsch = st.text_input("Was soll ich auf dem Server tun?")

            if wunsch:

                # GPT interpretiert den Wunsch
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Du bist ein Linux Server Agent. Antworte nur mit dem passenden Linux Befehl."
                        },
                        {
                            "role": "user",
                            "content": wunsch
                        }
                    ]
                )

                command = res.choices[0].message.content.strip()

                st.write("Auszuführender Befehl:")
                st.code(command)

                # SSH ausführen
                stdin, stdout, stderr = ssh.exec_command(command)

                output = stdout.read().decode()
                error = stderr.read().decode()

                if output:
                    st.write("Output:")
                    st.code(output)

                if error:
                    st.error(error)

        except Exception as e:
            st.error(f"SSH Fehler: {e}")
