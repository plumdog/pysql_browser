import sys

import plumbum
from pymysql import connect as mysql_connect
from pymysql.err import ProgrammingError as QueryError


# We start an ssh tunnel that links a remote port with a local one. We
# can then connect to the database as if it were local. We need an SSH
# connection to the remote machine as well as mysql login details.

# Possibly need to tell ssh-add (DISPLAY and SSH_ASKPASS) that we
# don't need a dialog box for our SSHing.

def ssh_tunnel_spawn(local_port, remote_user, remote_server, remote_port, remote_password):
    """This spawns the tunnelling process."""
    print('open SSH Machine')
    rem = plumbum.SshMachine(remote_server, user=remote_user, password=remote_password)
    print('open Tunnel')
    tun = rem.tunnel(local_port, remote_port)
    print('Tunnel spawned')
    return (rem, tun)

def _mysql_connect(mysql_username, mysql_password, local_port):
    """This gives the command that we need to pass to sqlalchemy so
    that it knows how to connect to our database."""

    return 'mysql+pymysql://{mysql_username}:{mysql_password}@localhost:{local_port}'.format(
        mysql_username=mysql_username, mysql_password=mysql_password, local_port=local_port)

def mysql_connection(mysql_username, mysql_password, local_port):
    """This performs the connection and returns a connection object
    that we can use to execute our SQL commands."""
    return mysql_connect(user=mysql_username, passwd=mysql_password, port=local_port)


class TunnelledMySQL(object):
    """A class so that we can use the 'with' statement and both the
    database connection, and the SSH tunnelling process will be closed
    if anything goes wrong, or if we are just done with the
    connection."""
    def __init__(self, local_port=3307, remote_user='root', remote_server='host.com', remote_port=3306, remote_password='', mysql_username='root', mysql_password=''):
        self.local_port = local_port
        self.remote_user = remote_user
        self.remote_server = remote_server
        self.remote_port = remote_port
        self.remote_password = remote_password
        self.mysql_username = mysql_username
        self.mysql_password = mysql_password

        self.rem = None
        self.tun = None
        self.connection = None

        self.enter_ok = True

    def __enter__(self):
        try:
            self.rem, self.tun = ssh_tunnel_spawn(self.local_port, self.remote_user, self.remote_server, self.remote_port, self.remote_password)
            self.connection = mysql_connection(self.mysql_username, self.mysql_password, self.local_port)
        except Exception:
            if self.__exit__(*sys.exc_info()):
                self.enter_ok = False
            else:
                raise
        return self

    def __exit__(self, _type, value, traceback):
        self.close()

    def close(self):
        if self.connection:
            self.connection.close()
        if self.tun:
            self.tun.close()
        if self.rem:
            self.rem.close()
