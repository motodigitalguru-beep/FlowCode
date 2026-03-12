import paramiko

class SSHManager:
    def __init__(self, hostname, username, password):
        self.hostname = '187.124.28.197'
        self.username = 'root'
        self.password = 'Mephisto10.11.1975?'
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.hostname, username=self.username, password=self.password)
        return True

    def execute(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode() + stderr.read().decode()

    def close(self):
        if self.client:
            self.client.close()
