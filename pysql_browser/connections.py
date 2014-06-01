from collections import namedtuple

Connection = namedtuple(
    'Connection',
    ['name', 'local_port', 'remote_user', 'remote_server', 'remote_port',
     'remote_password', 'mysql_username', 'mysql_password'])
