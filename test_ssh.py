import paramiko

# Verbindungsdaten
hostname = '187.124.28.197'
username = 'root'
password = 'Mephisto10.11.1975?' # Hier dein Passwort eintragen

def check_connection():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Verbinde zu FlowCode...")
        ssh.connect(hostname, username=username, password=password)
        
        # Testbefehl: Zeige alle laufenden Docker-Container
        stdin, stdout, stderr = ssh.exec_command('docker ps')
        print("\n--- Laufende Docker Container ---")
        print(stdout.read().decode())
        
        ssh.close()
        print("\nVerbindung erfolgreich!")
    except Exception as e:
        print(f"\nFehler bei der Verbindung: {e}")

if __name__ == "__main__":
    check_connection()
