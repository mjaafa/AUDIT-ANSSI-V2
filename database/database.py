import logging
import psycopg2
from pymongo import MongoClient

logger = logging.getLogger()

class mongoDb():
    def __init__(self, configuration):
        self.client = MongoClient(configuration.getStorageHost(),
                                  username=configuration.getStorageUser(),
                                  password=configuration.getStoragePassword(),
                                  authMechanism='PLAIN')
        self.collection = None

    def createDatabases(self):
        try:
            self.database = self.client["devices"]
            self.collection = self.database["CPE"]
        except Exception as e:
            logger.error("Create database failed: %s", e)

    def insertElement(self, element):
        try:
            self.collection.insert_one(element)
        except Exception as e:
            logger.error("Insert element failed: %s", e)


class store():
    def __init__(self, configuration):
        logging.info("Connecting to database")
        self.connection = psycopg2.connect(
            host=configuration.getStorageHost(),
            user=configuration.getStorageUser(),
            password=configuration.getStoragePassword()
        )
        try:
            cur = self.connection.cursor()
            cur.execute('SELECT version()')
            version = cur.fetchone()
            logging.debug('PostgreSQL database version: %s', version)
            cur.close()
        except Exception as e:
            logging.error('PostgreSQL database version check failed: %s', e)
