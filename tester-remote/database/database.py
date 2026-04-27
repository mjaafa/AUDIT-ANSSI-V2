import psycopg2
from pymongo import MongoClient

class mongoDb():
    def __init__(self, configuration):
        self.client = MongoClient(configuration.getStorageHost(),
                                  user=configuration.getStorageUser(),
                                  password=configuration.getStoragePassword(),
                                  authMechanism='PLAIN')

    def createDatabases(self):
        try :
            self.database = self.client["devices"]
            self.collection = self.database["CPE"]

        except Exception as e :
            logger.error("Create database")

    def insertElement(self, database, element):
        try :
            self.collection.insert_one[element]
        except Exception as e :
            logger.error("Insert element fails")



class store():
    def __init__(self, configuration):
        logging.info("Connecting to database")
        self.connection = psycopg2.connect( host=configuration.getStorageHost(),
                                            user=configuration.getStorageUser(),
                                            password=configuration.getStoragePassword())
        
        try :
            self.connection.cursor().execute('SELECT version()')
            logging.debug('PostgreSQL database version:', self.connection.cursor().fetchone())
        except Exception as e :
            logging.error('PostgreSQL database : no version %s ',e );
