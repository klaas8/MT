from sqlitedict import SqliteDict

class AppPreferences:
    _instance = None
    
    def __new__(cls, db_path="app_prefs.sqlite"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db = SqliteDict(db_path, autocommit=True)
        return cls._instance
    
    def get(self, key, default=None):
        return self.db.get(key, default)
    
    def put(self, key, value):
        self.db[key] = value
        self.db.commit()
    
    def remove(self, key):
        if key in self.db:
            del self.db[key]
            self.db.commit()
    
    def clear(self):
        self.db.clear()
        self.db.commit()
    
    def close(self):
        self.db.close()
        self._instance = None

prefs = AppPreferences()