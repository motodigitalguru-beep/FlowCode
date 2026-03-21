import paramiko

class SSHManager:
    def __init__(self, host, user, password, port=22):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, port=self.port, username=self.user, password=self.password)

    def execute(self, command):
        if not self.client:
            raise Exception("Nicht verbunden. Bitte zuerst connect() aufrufen.")
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode('utf-8')

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
