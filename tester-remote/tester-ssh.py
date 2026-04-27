import logging
from logging.config import fileConfig
from Colorer import colorer

from configuration.readConfiguration import readConfiguration
from connectivity.device import device
import datetime

# package configuration
fileConfig('log_conf.ini')
logger = logging.getLogger()


logger.setLevel(logging.DEBUG);

logger.debug(" configurations setup for  device ");
project = device()

project.connect()
#project.check()
print("# Resultats AUDIT", project.getConfigurations().getOrganism());
print("# White Paper Name :   ", project.getConfigurations().getWhitePaperName());
print("# White Paper Version : ", project.getConfigurations().getWhitePaperVersion());
print(" Tester Name :",  project.getConfigurations().getExecuter() + "<br>")
project.checkVersion();
now = datetime.datetime.now()
print(" Time : ", now.strftime("%Y-%m-%d %H:%M:%S"))
print("  ")            
logging.info("                             Definitions Test                           | ANSII Test | Res ");
logger.info("-------------------------------------------------------------------------|------------|----");
for idx in range(0, int(project.getnumberOfCommands())):
    project.execCommand(idx);

project.disconnect()

#database = store(project.getConfigurations())

