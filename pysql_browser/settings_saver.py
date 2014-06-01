import os
import shelve

PYSQL_DIR = '.pysql_browser'
PYSQL_FILE = 'config.db'

def get_shelf(writeback=False):
    hd = os.path.expanduser('~')
    d = os.path.join(hd, PYSQL_DIR)
    try:
        os.mkdir(d)
    except OSError:
        pass

    p = os.path.join(d, PYSQL_FILE)
    return shelve.open(p, writeback=writeback)
    

def save(key, value):
    with get_shelf(writeback=True) as s:
        s[key] = value
        s.sync()

def load(key, default=None):
    with get_shelf() as s:
        try:
            return s[key]
        except KeyError:
            return default
