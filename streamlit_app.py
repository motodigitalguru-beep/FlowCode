import streamlit as st
import paramiko
from groq import Groq

# 1. Seite konfigurieren
st.set_page_config(page_title="FlowCode Agent", page_icon="🤖", layout="centered")
st.title("🤖 FlowCode Server Agent")

# 2. Daten aus den Secrets laden (müssen in Streamlit hinterlegt sein)
groq_key = st.secrets.get("GROQ_API_KEY", "")
ssh_host = st.secrets.get("SSH_HOST", "187.124.28.197")
ssh_user = st.secrets.get("SSH_USER", "root")
ssh_pass = st.secrets.get("SSH_PASS", "")

# 3. Client Initialisierung
client = None
if groq_key:
    client = Groq(api_key=groq_key)

# Chat-Historie im Speicher behalten
if "messages" not in st.session_state:
    st.session_state.messages = []

# Verlauf anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Eingabe-Logik
if prompt := st.chat_input("Was soll ich auf dem Server tun?"):
    if not client or not ssh_pass:
        st.error("❌ Fehler: Keys oder SSH-Passwort fehlen in den Streamlit Secrets!")
    else:
        # User-Eingabe anzeigen
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("KI generiert Befehl..."):
            try:
                # KI-Anfrage mit strengen Anweisungen
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Du bist ein präziser Terminal-Übersetzer. "
                                "Antworte AUSSCHLIESSLICH mit dem validen Linux-Befehl. "
                                "KEINE Einleitung, KEIN 'Hier ist der Befehl', KEINE Backticks. "
                                "Hänge an jeden Befehl zwingend ' 2>/dev/null' an, um Fehler zu unterdrücken."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Nur die erste Zeile nehmen, falls die KI doch plaudert
                raw_cmd = res.choices[0].message.content.strip()
                cmd = raw_cmd.split('\n')[0].replace('```bash', '').replace('```', '').strip()

                with st.chat_message("assistant"):
                    st.code(f"# Ausführung:\n{cmd}")
                    
                    # SSH Verbindung aufbauen
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
                    
                    # Befehl in einer Login-Shell ausführen für korrekte Pfade
                    stdin, stdout, stderr = ssh.exec_command(f"bash -l -c '{cmd}'")
                    
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    
                    if output:
                        st.success("✅ Ergebnis:")
                        st.text(output)
                    if error:
                        # Da wir 2>/dev/null nutzen, sollten hier kaum Fehler kommen
                        st.warning("⚠️ Hinweis vom Server:")
                        st.text(error)
                        
                    if not output and not error:
                        st.info("Befehl wurde ohne Rückmeldung ausgeführt.")
                        
                    ssh.close()
                    
                    # Antwort in Verlauf speichern
                    st.session_state.messages.append({"role": "assistant", "content": f"Befehl ausgeführt: `{cmd}`"})

            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")

# Footer Info
st.sidebar.markdown("---")
st.sidebar.info("💡 Nutze natürliche Sprache, um den Server zu steuern.")
