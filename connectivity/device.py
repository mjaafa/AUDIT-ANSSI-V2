import paramiko
import logging
from configuration.readConfiguration import readConfiguration

logger = logging.getLogger()

class device():
    def __init__(self, username, password, json=False):
        self.remoteConfiguration = readConfiguration()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.username = username
        self.password = password
        self.json = json

    def getnumberOfCommands(self):
        return self.remoteConfiguration.getnumberOfCommands()

    def connect(self):
        hostname = self.remoteConfiguration.getHostname()
        logging.debug("Connecting to device... %s", hostname)
        try:
            if not self.json:
                self.client.connect(hostname, username=self.username, password=self.password)
            else:
                self.client.connect(hostname,
                                    username=self.remoteConfiguration.getUsername(),
                                    password=self.remoteConfiguration.getPassword())
        except Exception as e:
            logging.error("Could not connect to device: %s", e)
            raise

    def execCommand(self, commandIdx):
        try:
            cmd = self.remoteConfiguration.getCommand(commandIdx)
            expected = self.remoteConfiguration.getRule(commandIdx)
            desc = self.remoteConfiguration.getDescription(commandIdx)

            _, stdout, _ = self.client.exec_command(cmd)
            result = stdout.read().decode(errors='replace').strip()

            if result == expected:
                logger.info(" %s <span style='color: green;'>OK</span>  ", desc)
            else:
                logger.error(" %s <span style='color: red;'>KO</span>  ", desc)
        except Exception as e:
            logging.error("Command %d failed: %s", commandIdx, e)

    def check(self):
        try:
            n = self.remoteConfiguration.getnumberOfCommands()
            logging.debug("SSH session login successful, number of commands: %d", n)
            for commandIdx in range(n):
                cmd = "sudo " + self.remoteConfiguration.getCommand(commandIdx)
                _, stdout, _ = self.client.exec_command(cmd)
                stdout.read()
        except Exception as e:
            logging.error("Command execution failed: %s", e)

    def getSession(self):
        return self.client

    def getConfigurations(self):
        return self.remoteConfiguration

    def disconnect(self):
        try:
            logger.info("Disconnecting")
            self.client.close()
        except Exception as e:
            logger.error("Could not disconnect: %s", e)
