import streamlit as st
import os
from core.ssh_client import SSHManager

# Layout der Seite
st.title("📊 Server Dashboard")
st.markdown("Live-Überwachung deiner Infrastruktur")

# Zugangsdaten sicher aus der .env holen
host = os.getenv("SSH_HOST")
user = os.getenv("SSH_USER")
password = os.getenv("SSH_PASS")

# B2B Info-Box
st.info(f"Aktuelles Zielsystem: **{host}** (User: {user})")

# Button zum manuellen Aktualisieren (verhindert ständige Ladezeiten)
if st.button("🔄 System-Status abfragen", type="primary"):
    with st.spinner(f"Verbinde mit {host} via Clawbot..."):
        # Hier erschaffen wir den Clawbot mit den geheimen Daten!
        ssh = SSHManager(host, user, password)
        
        try:
            ssh.connect()
            
            # 1. RAM Auslastung abfragen (gibt den %-Wert zurück)
            ram_cmd = "free -m | awk 'NR==2{printf \"%.0f\", $3*100/$2 }'"
            ram_usage = ssh.execute(ram_cmd).strip()
            
            # 2. CPU Load (1-Minuten-Durchschnitt)
            cpu_cmd = "uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f1 | awk '{$1=$1};1'"
            cpu_load = ssh.execute(cpu_cmd).strip()

            # 3. N8N / Docker Status prüfen
            docker_cmd = "docker ps --format '{{.Names}} ({{.Status}})'"
            docker_status = ssh.execute(docker_cmd).strip()
            
            ssh.close()

            # --- ERGEBNISSE ANZEIGEN (Das sieht richtig professionell aus) ---
            st.success("Verbindung erfolgreich! Live-Daten empfangen.")
            
            # Kennzahlen in Spalten aufteilen
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="RAM Auslastung", value=f"{ram_usage} %")
            with col2:
                st.metric(label="CPU Load (1 Min)", value=cpu_load)
            with col3:
                # Simples Ampelsystem für n8n
                if "n8n" in docker_status.lower():
                    st.metric(label="n8n Status", value="🟢 Online")
                else:
                    st.metric(label="n8n Status", value="🔴 Offline/Nicht gefunden")

            # Detail-Ansicht für Docker
            st.markdown("### 🐳 Laufende Docker-Container")
            if docker_status:
                st.code(docker_status, language="bash")
            else:
                st.warning("Keine laufenden Container gefunden oder Docker ist nicht installiert.")

        except Exception as e:
            st.error(f"🔴 Verbindungsfehler: {e}")
