import streamlit as st

st.title("🔍 Diagnose-Modus")

# Wir listen hier einfach mal auf, was die App "sieht"
st.write("Suche nach Zugangsdaten...")

keys_im_system = list(st.secrets.keys())
st.write("Gefundene Schlüssel in den Secrets:", keys_im_system)

if "SSH_HOST" in st.secrets:
    st.success("✅ SSH_HOST wurde gefunden!")
else:
    st.error("❌ SSH_HOST fehlt in den Secrets!")

if "APP_PASSWORD" in st.secrets:
    st.success("✅ APP_PASSWORD wurde gefunden!")
else:
    st.error("❌ APP_PASSWORD fehlt in den Secrets!")

st.info("Wenn hier 'fehlt' steht, obwohl du es im Browser eingetragen hast, klicke im Browser nochmal auf 'Save' und lade die App neu.")
