import sys
import os
dirAddon= os.path.dirname(__file__)
sys.path.append(dirAddon)
sys.path.append(os.path.join(dirAddon, "lib"))
if sys.version.startswith("3.11"):
    sys.path.append(os.path.join(dirAddon, "lib", "_311"))
    from .lib._311 import sqlite3 
    sqlite3.__path__.append(os.path.join(dirAddon, "lib", "_311", "sqlite3"))
else:
    sys.path.append(os.path.join(dirAddon, "lib", "_37"))
    from .lib._37 import sqlite3
    sqlite3.__path__.append(os.path.join(dirAddon, "lib", "_37", "sqlite3"))
del sys.path[-3:]
class database:
    def __init__(self, DBName):
        self.db = sqlite3.connect(DBName)
        self.cursor = self.db.cursor()
        self.modifiedRows = 0
        self.autoCommit = False
    def close(self):
        if self.db is not None:
            self.cursor.close()
            self.db.close()
            self.cursor = None
            self.db = None
            self.modifiedRows = 0
    def open(self, DBName):
        if self.db is None:
            self.db = sqlite3.connect(DBName)
            self.cursor = self.db.cursor()
    def execute(self, query, values = (), rowsAmount=-1):
        try:
            self.cursor.execute(query, values)
            results = []
            if rowsAmount == -1:
                results = self.cursor.fetchall()
            elif rowsAmount == 0:
                results = self.cursor.fetchone()
            elif rowsAmount >= 1:
                results = self.cursor.fetchmany(rowsAmount)
            self.modifiedRows = self.cursor.rowcount
            if self.autoCommit:
                self.db.commit()
            return results
        except sqlite3.OperationalError as e:
            print(e)
    def create(self, tableName, params):
        try:
            self.execute(f"create table if not exists {tableName}({params})")
        except sqlite3.OperationalError as e:
            print(e)
    def commit(self):
        try:
            self.db.commit()
        except sqlite3.OperationalError as e:
            print(e)
def rollback(self):
        try:
            self.db.rollback()
        except sqlite3.OperationalError as e:
            print(e)