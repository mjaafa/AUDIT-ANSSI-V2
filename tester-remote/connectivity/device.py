from pexpect import pxssh
import logging
from configuration.readConfiguration import readConfiguration
logger = logging.getLogger()

class device ():
    def __init__(self):
        self.remoteConfiguration = readConfiguration()
        self.session = pxssh.pxssh(timeout=None)
        
    def getnumberOfCommands(self):
        return self.remoteConfiguration.getnumberOfCommands()

    def connect(self):
        #logging.debug("Connecting to device... %s", self.remoteConfiguration.getHostname())
        try:
            self.session.login(self.remoteConfiguration.getHostname(),
                               self.remoteConfiguration.getUsername(),
                               self.remoteConfiguration.getPassword())
        except Exception:
            logging.error("Could not connect to device")

    def getSession(self):
        logging.debug("Getting session");
        return self.session;

    def check(self):
        #self.database = mongoDb(project.getConfigurations())
        #self.database = store(project.getConfigurations())
        try:
            #logging.debug("SSH session login successful number of commands : %d",int(self.remoteConfiguration.getnumberOfCommands()))

            for commandIdx in range(int(self.remoteConfiguration.getnumberOfCommands())):
                self.session.sendline (self.remoteConfiguration.getCommand(commandIdx))
                self.session.prompt()
                ##logger.debug(">>> %s", self.remoteConfiguration.getCommand(commandIdx))
                #logger.debug(">>> %s", self.remoteConfiguration.getDescription(commandIdx))
                #logger.debug("%s", self.session.before.decode())
                #logger.debug("%s", self.session.before.decode().splitlines(0)[2:])
                ##element="{\""+self.remoteConfiguration.getDescription(commandIdx)+"\":\""+str(self.session.before.decode()).splitlines(0)[2]+"\"}"
                ##logger.debug("%s", element)
                #:mongoDb.insertElement(element)

        except Exception:
                logging.error("Could not connect to device")

    def checkVersion(self):
        #self.database = mongoDb(project.getConfigurations())
        #self.database = store(project.getConfigurations())
        try:
            #logging.debug("SSH session login successful number of commands : %d",int(self.remoteConfiguration.getnumberOfCommands()))
            
            self.session.sendline ("cat /var/os-version")
            self.session.prompt()
                ##logger.debug(">>> %s", self.remoteConfiguration.getCommand(commandIdx))
                #logger.debug(">>> %s", self.remoteConfiguration.getDescription(commandIdx))
                #logger.debug("%s", self.session.before.decode())
                #logger.debug("%s", self.session.before.decode().splitlines(0)[2:])
                ##element="{\""+self.remoteConfiguration.getDescription(commandIdx)+"\":\""+str(self.session.before.decode()).splitlines(0)[2]+"\"}"
            print("# Software ",str(self.session.before.decode().split('\r\n')[2]))
                #:mongoDb.insertElement(element)

        except Exception:
                logging.error("Could not connect to device")

    def execCommand(self, commandIdx):
        try:
            self.session.sendline (self.remoteConfiguration.getCommand(commandIdx));
            self.session.prompt()
            ##logger.debug(">>> %s", self.remoteConfiguration.getCommand(commandIdx))
            #logger.debug(">>> %s", self.remoteConfiguration.getDescription(commandIdx))
            #logger.debug("%s", self.session.before.decode())
            #logger.debug("%s", self.remoteConfiguration.getRule(commandIdx))
            #logger.debug("%s", self.session.before.decode().split('\r\n')[1])
            if(self.session.before.decode().split('\r\n')[1] == self.remoteConfiguration.getRule(commandIdx)):
                logger.info(" %s <span style='color: green;'>OK</span>  ", self.remoteConfiguration.getDescription(commandIdx))
            else:
                logger.error(" %s <span style='color: red;'>KO</span>  ", self.remoteConfiguration.getDescription(commandIdx))
            

        except Exception:
            logging.error(" Could not connect to device")

    def getConfigurations(self):
        return self.remoteConfiguration
    
    def disconnect(self): 
        try :
            logger.info("Disconnecting")
            self.session.logout()
        except Exception:
            logger.error("Could not disconnect")
