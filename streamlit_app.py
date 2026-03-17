import streamlit as st
import paramiko
from groq import Groq
# import os # dotenv wird in der Cloud nicht benötigt, da wir Secrets nutzen
# from dotenv import load_dotenv

# load_dotenv() # Nicht für die Cloud

st.set_page_config(page_title="FlowCode Agent", page_icon="🤖")
st.title("🤖 FlowCode Server Agent")

# Sidebar für Login-Daten
with st.sidebar:
    st.header("⚙️ Login")
    # Platzhalter für IP und Keys - die musst du dann in der Sidebar eingeben!
    ssh_host = st.text_input("Server IP", value="0.0.0.0") # Beispiel IP
    ssh_user = st.text_input("Benutzer", value="root")
    ssh_pass = st.text_input("SSH Passwort", type="password")
    
    # Platzhalter für den Groq Key - auch in der Sidebar einzugeben!
    groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

# --- NEU & WICHTIG: Client-Initialisierung sichern ---
client = None
if groq_key:
    # Der Client wird NUR erstellt, wenn ein Key eingetippt wurde
    client = Groq(api_key=groq_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat-Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Eingabe-Logik
if prompt := st.chat_input("Was soll ich auf dem Server tun?"):
    # Prüfen, ob wir überhaupt bereit sind
    if not client:
        st.error("❌ Fehler: Bitte gib zuerst den Groq API Key in der Sidebar ein!")
    elif not ssh_pass:
        st.error("❌ Fehler: Bitte gib zuerst das SSH-Passwort in der Sidebar ein!")
    elif ssh_host == "0.0.0.0":
        st.error("❌ Fehler: Bitte gib zuerst deine korrekte Server IP in der Sidebar ein!")
    else:
        # Alles bereit, Befehl verarbeiten
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Groq denkt nach..."):
            try:
                # KI-Anfrage an Groq (Llama 3 Modell)
                res = client.chat.completions.create(
                    model="llama3-8b-8192", # Ein schnelles Groq Modell
                    messages=[
                        {"role": "system", "content": "Antworte NUR mit dem Linux-Befehl."},
                        {"role": "user", "content": prompt}
                    ]
                )
                cmd = res.choices[0].message.content.strip().replace('```bash', '').replace('```', '')

                with st.chat_message("assistant"):
                    st.info(f"Führe aus: `{cmd}`")
                    
                    # SSH Verbindung aufbauen
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                    
                    # Befehl auf dem Server ausführen
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    out = stdout.read().decode()
                    err = stderr.read().decode()
                    
                    # Ergebnisse im Chat anzeigen
                    if out: st.code(out)
                    if err: st.error(err)
                    ssh.close()
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
