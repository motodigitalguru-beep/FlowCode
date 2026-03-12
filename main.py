from ssh_client import SSHManager
from openai import OpenAI

# Deine Konfiguration
client = OpenAI(api_key="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")
ssh = SSHManager('187.124.28.197', 'root', 'Mephisto10.11.1975?')

def main():
    if ssh.connect():
        print("--- FlowCode Verbunden ---")
        user_wunsch = input("Was soll ich tun? ")
        
        # KI entscheidet
        prompt = f"Du bist Admin. User will: {user_wunsch}. Gib nur den Linux-Befehl aus."
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        befehl = response.choices[0].message.content.strip()
        
        print(f"Führe aus: {befehl}")
        print(ssh.execute(befehl))
        ssh.close()

if __name__ == "__main__":
    main()
