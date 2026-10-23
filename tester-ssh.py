import logging
from logging.config import fileConfig
from Colorer import colorer
import argparse
import getpass
from connectivity.device import device
from report.report import generate
import datetime

fileConfig('log_conf.ini')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description="ANSSI audit report")
parser.add_argument('username', type=str, help='SSH username')
parser.add_argument('--password', type=str, default=None,
                    help='SSH password (prompted securely if omitted)')
parser.add_argument('--port', type=int, default=None,
                    help='SSH port (default: "port" in configDevice.json, else 22)')
parser.add_argument('--key', type=str, default=None,
                    help='Private key file (default: "key_filename" in configDevice.json)')
parser.add_argument('--cert', type=str, default=None,
                    help='OpenSSH certificate (*-cert.pub) for the private key (default: "certificate" in configDevice.json)')
parser.add_argument('--sudo-password', type=str, default=None,
                    help='sudo password on the target (default: SSH password; prompted when using a key)')
parser.add_argument('--out', type=str, default='reports',
                    help='Output directory for generated reports (default: reports/)')
args = parser.parse_args()

logger.debug("Configuration setup for device")
project = device(args.username, args.password, False, port=args.port,
                 key_filename=args.key, certificate=args.cert)
if not project.key_filename:
    project.password = args.password or getpass.getpass('SSH password: ')
project.sudoPassword = args.sudo_password
if project.key_filename and not project.sudoPassword:
    project.sudoPassword = getpass.getpass('sudo password (empty for NOPASSWD): ') or None

project.connect()

now = datetime.datetime.now()
print("# Resultats AUDIT ANSSI")
print("Time:", now.strftime("%Y-%m-%d %H:%M:%S"))
print()
logging.info("                             Definitions Test                           | ANSII Test | Res")
logger.info("-------------------------------------------------------------------------|------------|----")

results = []
for idx in range(project.getnumberOfCommands()):
    result = project.execCommand(idx)
    if result:
        results.append(result)

project.disconnect()

hostname = project.getConfigurations().getHostname()
md_path, pdf_path = generate(results, hostname, out_dir=args.out)
print(f"\nReports saved:")
print(f"  Markdown : {md_path}")
print(f"  PDF      : {pdf_path}")
