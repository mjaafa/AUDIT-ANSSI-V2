import logging
from logging.config import fileConfig
import json
import pyjq
logger = logging.getLogger()

class readConfiguration():
    data = [];
    def __init__(self):
        #logging.debug("read configuration")
        # read json file configuration
        fileConfig = open('configDevice.json');
        self.data = json.load(fileConfig);
    def getStorageHost(self):
        return ' '.join(pyjq.all(".device[0].storageDatabase[0].hostname", self.data))

    def getStorageUser(self):
        return ' '.join(pyjq.all(".device[0].storageDatabase[0].username", self.data))

    def getStoragePassword(self):
        return ' '.join(pyjq.all(".device[0].storageDatabase[0].password", self.data))

    def getStorageDatabase(self):
        return ' '.join(pyjq.all(".device[0].storageDatabase[0].database", self.data))

    def getHostname(self):
        return ' '.join(pyjq.all(".device[0].configuration[0].hostname",self.data))

    def getUsername(self):
        return ' '.join(pyjq.all(".device[0].configuration[0].username",self.data))

    def getPassword(self):
        return ' '.join(pyjq.all(".device[0].configuration[0].password",self.data))

    def getCommands(self):
        return pyjq.all(".device[0].commands",self.data)

    def getnumberOfCommands(self):
        #return pyjq.all(".device[0].numberOfCommands",self.data)
        return ' '.join(pyjq.all(".device[0].numberOfCommands",self.data))

    def getCommand(self, index):
        retrieve = ".device[0].commands["+str(index)+"].command"
        return ' '.join(pyjq.all(retrieve,self.data))

    def getDescription(self, index):
        retrieve = ".device[0].commands["+str(index)+"].Description"
        return ' '.join(pyjq.all(retrieve,self.data))

    def getRule(self, index):
        retrieve = ".device[0].commands["+str(index)+"].rule"
        return ' '.join(pyjq.all(retrieve,self.data))

    def getOrganism(self):
        return ' '.join(pyjq.all(".device[0].auditInfo[0].organismName", self.data))

    def getExecuter(self):
        return ' '.join(pyjq.all(".device[0].auditInfo[0].executer", self.data))
    
    def getWhitePaperVersion(self):
        return ' '.join(pyjq.all(".device[0].auditInfo[0].whitePaperVersion", self.data))
    
    def getWhitePaperName(self):
        return ' '.join(pyjq.all(".device[0].auditInfo[0].whitePaperName", self.data))