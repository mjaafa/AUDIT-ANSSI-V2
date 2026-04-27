import logging
from logging.config import fileConfig
from Colorer import colorer
import argparse
import getpass
from configuration.readConfiguration import readConfiguration
from connectivity.device import device
import datetime

fileConfig('log_conf.ini')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description="ANSSI audit report (markdown)")
parser.add_argument('username', type=str, help='SSH username')
parser.add_argument('--password', type=str, default=None,
                    help='SSH password (prompted securely if omitted)')
args = parser.parse_args()
password = args.password or getpass.getpass('SSH password: ')

logger.debug("Configuration setup for device")
project = device(args.username, password, False)

project.connect()
print("# Resultats AUDIT ANSSI")
now = datetime.datetime.now()
print("Time:", now.strftime("%Y-%m-%d %H:%M:%S"))
print()
logging.info("                             Definitions Test                           | ANSII Test | Res")
logger.info("-------------------------------------------------------------------------|------------|----")
for idx in range(project.getnumberOfCommands()):
    project.execCommand(idx)

project.disconnect()
