import streamlit as st
import paramiko
from groq import Groq

# --- DEINE DATEN DIREKT HIER (Wie auf dem Rechner) ---
GROQ_API_KEY = "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"
SSH_HOST = "187.124.28.197"
SSH_USER = "root"
SSH_PASS = "FlowCode20.26"

st.set_page_config(page_title="FlowCode Agent", page_icon="🤖")
st.title("🤖 FlowCode Server Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Was soll ich tun?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("KI arbeitet..."):
        try:
            # Hier nutzen wir die fest hinterlegten Keys
            client = Groq(api_key=GROQ_API_KEY)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                          {"role": "user", "content": prompt}]
            )
            cmd = res.choices[0].message.content.strip().replace('```bash', '').replace('```', '')

            with st.chat_message("assistant"):
                st.info(f"Befehl: {cmd}")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS)
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out, err = stdout.read().decode(), stderr.read().decode()
                if out: st.success(out)
                if err: st.error(err)
                ssh.close()
        except Exception as e:
            st.error(f"Fehler: {e}")
