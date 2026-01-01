from sqlitedict import SqliteDict
import os
import atexit
from pathlib import Path
from datetime import datetime
import pytz

class Preferences:
    _instance = None
    _db_path = ""

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if db_path is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(current_dir, "prefs.sqlite")
            else:
                if not os.path.isabs(db_path):
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    db_path = os.path.join(current_dir, db_path)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            cls._instance._db_path = db_path
            cls._instance.db = SqliteDict(db_path, autocommit=True)
            atexit.register(cls._instance.close)
        return cls._instance

    def get(self, key, default=None):
        try:
            return self.db.get(key, default)
        except Exception:
            return default

    def put(self, key, value):
        self.db[key] = value
        self.db.commit()
        self.save()

    def remove(self, key):
        if key in self.db:
            del self.db[key]
            self.db.commit()
            self.save()

    def clear(self):
        self.db.clear()
        self.db.commit()
        self.save()

    def keys(self):
        return list(self.db.keys())

    def items(self):
        return list(self.db.items())

    def __contains__(self, key):
        return key in self.db

    def close(self):
        if hasattr(self, 'db'):
            self.db.close()
        self.__class__._instance = None

    def __del__(self):
        self.close()

    def get_db_path(self):
        return self._db_path

    def getTime(self):
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        formatted_date = now.strftime('%Y-%m-%d')
        return formatted_date

    def getTimes(self):
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date

    def save(self):
        db_path = self.get_db_path()
        if os.path.exists(db_path):
            try:
                if os.system(f'git add "{db_path}"') == 0:
                    os.system('git config --local user.name "github-actions[bot]"')
                    os.system('git config --local user.email "github-actions[bot]@users.noreply.github.com"')
                    os.system('git commit -m "更新数据库文件"')
                    os.system('git push --quiet --force-with-lease')
            except Exception as e:
                print(f"Git操作失败: {e}")


prefs = Preferences()