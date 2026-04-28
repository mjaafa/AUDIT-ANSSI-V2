import logging
import json
import os
import sys

logger = logging.getLogger()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))

class readConfiguration():
    def __init__(self):
        logging.debug("read configuration")
        base_path = get_base_path()
        config_path = os.path.join(base_path, '../configDevice.json')
        with open(config_path, 'r') as file:
            self.data = json.load(file)
        self._device = self.data['device'][0]
        self._commands = self._device['commands']

    def getStorageHost(self):
        return self._device['storageDatabase'][0]['hostname']

    def getStorageUser(self):
        return self._device['storageDatabase'][0]['username']

    def getStoragePassword(self):
        return self._device['storageDatabase'][0]['password']

    def getStorageDatabase(self):
        return self._device['storageDatabase'][0]['database']

    def getHostname(self):
        return self._device['configuration'][0]['hostname']

    def getUsername(self):
        return self._device['configuration'][0]['username']

    def getPassword(self):
        return self._device['configuration'][0]['password']

    def getCommands(self):
        return self._commands

    def getnumberOfCommands(self):
        return len(self._commands)

    def getCommand(self, index):
        return self._commands[index]['command']

    def getDescription(self, index):
        return self._commands[index]['Description']

    def getRule(self, index):
        return self._commands[index]['rule']
