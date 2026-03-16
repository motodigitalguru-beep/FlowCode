import streamlit as st
import paramiko
from groq import Groq
from openai import OpenAI
import os

st.set_page_config(page_title="FlowCode AI Agent", page_icon="🚀")
st.title("🚀 FlowCode Multi-AI Agent")

with st.sidebar:
    st.header("⚙️ Konfiguration")
    ssh_host = st.text_input("Server IP", value="187.124.28.197")
    ssh_user = st.text_input("SSH Benutzer", value="root")
    ssh_pass = st.text_input("SSH Passwort", type="password")
    
    st.divider()
    ai_provider = st.radio("KI-Provider wählen:", ["OpenAI", "Groq"])
    api_key = st.text_input(f"{ai_provider} API Key", type="password")

if not ssh_pass or not api_key:
    st.warning("Bitte SSH-Passwort und API-Key in der Sidebar ergänzen.")
else:
    # Initialisierung des gewählten Providers
    if ai_provider == "OpenAI":
        client = OpenAI(api_key=api_key)
        model_name = "gpt-4-turbo" # oder "gpt-3.5-turbo"
    else:
        client = Groq(api_key=api_key)
        model_name = "llama-3.3-70b-versatile"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Was soll ich auf dem Server tun?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner(f"{ai_provider} denkt nach..."):
            try:
                if ai_provider == "OpenAI":
                    res = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                                  {"role": "user", "content": prompt}]
                    )
                else:
                    res = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                                  {"role": "user", "content": prompt}]
                    )
                cmd = res.choices[0].message.content.strip().replace('```bash', '').replace('```', '')
            except Exception as e:
                st.error(f"KI Fehler ({ai_provider}): {e}")
                st.stop()

        with st.chat_message("assistant"):
            st.info(f"Führe aus: {cmd}")
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out, err = stdout.read().decode(), stderr.read().decode()
                if out: st.code(out)
                if err: st.error(err)
                ssh.close()
            except Exception as e:
                st.error(f"SSH Fehler: {e}")
