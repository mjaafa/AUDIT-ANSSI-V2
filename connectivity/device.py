import paramiko
import logging
import getpass
import os
import shlex
from configuration.readConfiguration import readConfiguration

logger = logging.getLogger()

class device():
    def __init__(self, username, password, json=False, port=None, key_filename=None, certificate=None):
        self.remoteConfiguration = readConfiguration()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.username = username
        self.password = password
        self.json = json
        self.port = port if port is not None else self.remoteConfiguration.getPort()
        self.key_filename = key_filename or self.remoteConfiguration.getKeyFile()
        self.certificate = certificate or self.remoteConfiguration.getCertificate()
        self.sudoPassword = None

    def _loadKey(self):
        # Load the private key and attach the OpenSSH certificate to it
        path = os.path.expanduser(self.key_filename)
        passphrase = None
        for _ in range(2):
            for keyClass in (paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.RSAKey):
                try:
                    pkey = keyClass.from_private_key_file(path, password=passphrase)
                    break
                except paramiko.PasswordRequiredException:
                    passphrase = getpass.getpass('Passphrase for %s: ' % path)
                    pkey = None
                    break
                except paramiko.SSHException:
                    pkey = None
            if pkey is not None:
                break
        if pkey is None:
            raise paramiko.SSHException("Unsupported or unreadable private key: %s" % path)
        if self.certificate:
            cert = os.path.expanduser(self.certificate)
            logging.debug("Loading certificate %s", cert)
            pkey.load_certificate(cert)
        return pkey

    def _authArgs(self):
        if not self.key_filename:
            return {}
        return {'pkey': self._loadKey(), 'look_for_keys': False, 'allow_agent': False}

    def getnumberOfCommands(self):
        return self.remoteConfiguration.getnumberOfCommands()

    def connect(self):
        hostname = self.remoteConfiguration.getHostname()
        logging.debug("Connecting to device... %s:%s", hostname, self.port)
        try:
            auth = self._authArgs()
            if not self.json:
                self.client.connect(hostname, port=self.port, username=self.username, password=self.password, **auth)
            else:
                self.client.connect(hostname,
                                    port=self.port,
                                    username=self.remoteConfiguration.getUsername(),
                                    password=self.remoteConfiguration.getPassword(),
                                    **auth)
        except Exception as e:
            logging.error("Could not connect to device: %s", e)
            raise

    def _sudoExec(self, cmd):
        # Run the command through bash as root; the password is fed on stdin
        # (sudo -S), or sudo -n is used when no password is available (NOPASSWD)
        password = self.sudoPassword or self.password
        if password:
            wrapped = "sudo -S -p '' bash -c %s" % shlex.quote(cmd)
        else:
            wrapped = "sudo -n bash -c %s" % shlex.quote(cmd)
        stdin, stdout, stderr = self.client.exec_command(wrapped)
        if password:
            stdin.write(password + '\n')
            stdin.flush()
        out = stdout.read().decode(errors='replace').strip()
        err = stderr.read().decode(errors='replace').strip()
        if err:
            logging.debug("stderr for %r: %s", cmd, err)
        return out

    def execCommand(self, commandIdx):
        desc = self.remoteConfiguration.getDescription(commandIdx)
        name = self.remoteConfiguration.getName(commandIdx)
        try:
            cmd = self.remoteConfiguration.getCommand(commandIdx)
            expected = self.remoteConfiguration.getRule(commandIdx)

            result = self._sudoExec(cmd)
            ok = result == expected

            if ok:
                logger.info(" %s <span style='color: green;'>OK</span>  ", desc)
            else:
                logger.error(" %s <span style='color: red;'>KO</span>  ", desc)

            return {'name': name, 'description': desc, 'expected': expected, 'result': result, 'ok': ok}
        except Exception as e:
            logging.error("Command %d failed: %s", commandIdx, e)
            return {'name': name, 'description': desc, 'expected': '', 'result': '', 'ok': False}

    def check(self):
        try:
            n = self.remoteConfiguration.getnumberOfCommands()
            logging.debug("SSH session login successful, number of commands: %d", n)
            for commandIdx in range(n):
                self._sudoExec(self.remoteConfiguration.getCommand(commandIdx))
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
