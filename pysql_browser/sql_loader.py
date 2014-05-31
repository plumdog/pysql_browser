import sys
from os.path import dirname, join

class _SQLLoader(object):
    def __getattr__(self, file_name):
        file_dirname = dirname(__file__)
        path = join(file_dirname, 'sql', file_name + '.sql')
        with open(path) as f:
            return f.read().strip()

SQLLoader = _SQLLoader()
