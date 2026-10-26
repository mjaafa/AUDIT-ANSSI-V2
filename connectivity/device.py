import paramiko
import logging
import getpass
import os
import shlex
import json
import hashlib
import datetime
import difflib
from configuration.readConfiguration import readConfiguration

logger = logging.getLogger()

# Printed by a check that does not apply to the target (architecture, kernel version, ...)
NOT_APPLICABLE = "not applicable"
# Printed by a recommendation that cannot be verified automatically
MANUAL = "manual check"

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
        # Ask the auditor for the recommendations that need a human decision (dialog = Yes)
        self.interactive = False
        # Previous auditor answers, reused while the evidence they were based on is unchanged
        self.answersFile = None
        self.answers = {}

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
            comment = ''
            if self.remoteConfiguration.getDialog(commandIdx):
                if result == NOT_APPLICABLE:
                    status = 'N/A'
                else:
                    status, comment = self._manualDecision(desc, name, result)
            elif result == NOT_APPLICABLE:
                status = 'N/A'
            elif result == MANUAL:
                status = 'MANUAL'
            else:
                status = 'OK' if result == expected else 'KO'

            if status == 'OK':
                logger.info(" %s <span style='color: green;'>OK</span>  ", desc)
            elif status == 'N/A':
                logger.info(" %s <span style='color: grey;'>N/A</span>  ", desc)
            elif status == 'MANUAL':
                logger.info(" %s <span style='color: orange;'>MANUAL</span>  ", desc)
            else:
                logger.error(" %s <span style='color: red;'>KO</span>  ", desc)

            return {'name': name, 'description': desc, 'expected': expected, 'result': result,
                    'ok': status == 'OK', 'status': status, 'comment': comment}
        except Exception as e:
            logging.error("Command %d failed: %s", commandIdx, e)
            return {'name': name, 'description': desc, 'expected': '', 'result': '', 'ok': False, 'status': 'KO'}

    def loadAnswers(self, path):
        self.answersFile = path
        try:
            with open(path, encoding='utf-8') as f:
                self.answers = json.load(f)
        except FileNotFoundError:
            self.answers = {}

    def _saveAnswer(self, ref, status, comment, evidence):
        self.answers[ref] = {'status': status, 'comment': comment,
                             'date': datetime.date.today().isoformat(),
                             'host': self.remoteConfiguration.getHostname(),
                             'sha256': hashlib.sha256(evidence.encode()).hexdigest(),
                             'evidence': evidence}
        tmp = self.answersFile + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self.answers, f, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(tmp, self.answersFile)

    def _manualDecision(self, desc, name, evidence):
        # Reuse the saved answer when the evidence did not change, otherwise ask (or report MANUAL)
        ref = desc.split('|')[1].split()[-1] if '|' in desc else name
        saved = self.answers.get(ref)
        same = bool(saved) and saved.get('sha256') == hashlib.sha256(evidence.encode()).hexdigest()
        if not self.interactive:
            if same:
                note = "reviewed %s" % saved['date']
                return saved['status'], "%s: %s" % (note, saved['comment']) if saved['comment'] else note
            if saved:
                return 'MANUAL', "evidence changed since review of %s" % saved['date']
            return 'MANUAL', ''
        status, comment = self._askAuditor(desc, name, evidence, saved, same)
        if status != 'MANUAL' and self.answersFile:
            self._saveAnswer(ref, status, comment, evidence)
        return status, comment

    def _askAuditor(self, desc, name, evidence, saved=None, same=False):
        # Show what was collected on the target and let the auditor decide
        rule = desc.split('|')[1].strip() if '|' in desc else ''
        print("\n" + "=" * 78)
        print("%s - %s" % (rule, name))
        print(desc.split('|')[0].strip())
        print("-" * 78)
        print(evidence or "(no output)")
        print("-" * 78)
        answers = {'o': 'OK', 'k': 'KO', 'n': 'N/A', 's': 'MANUAL'}
        keep = ''
        if saved and same:
            print("Previous answer (%s): %s %s - evidence unchanged" % (saved['date'], saved['status'], saved['comment']))
            keep = " (Enter = keep %s)" % saved['status']
        elif saved:
            print("Previous answer (%s): %s %s - evidence CHANGED since:" % (saved['date'], saved['status'], saved['comment']))
            for line in difflib.unified_diff(saved.get('evidence', '').splitlines(), evidence.splitlines(),
                                             'reviewed', 'now', lineterm='', n=0):
                print("  " + line)
        print("-" * 78)
        while True:
            answer = input("Compliant? [o]k / [k]o / [n]ot applicable / [s]kip%s: " % keep).strip().lower()[:1]
            if answer == '' and keep:
                return saved['status'], saved['comment']
            if answer == '':
                answer = 's'
            if answer in answers:
                break
        if answers[answer] == 'MANUAL':
            return 'MANUAL', ''
        previous = saved['comment'] if saved else ''
        comment = input("Comment%s: " % (" [%s]" % previous if previous else " (optional)")).strip() or previous
        return answers[answer], comment

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
