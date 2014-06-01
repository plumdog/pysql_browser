from .settings_saver import save as settings_save, load as settings_load
from .connections import Connection
from keyring import set_password, get_password
import string
import random

KEY = 'connections'
SECRET_FIELDS = ['remote_password', 'mysql_password']
KEYRING_SYSTEM_NAME = 'pysql_browser'


def save(connections):
    enc_connections = [encode_connection(c) for c in connections]
    settings_save(KEY, enc_connections)


def load():
    enc_connections = settings_load(KEY, [])
    dec_connections = [decode_connection(c) for c in enc_connections]
    return dec_connections


def random_suffix(n=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


def store_new_secret(name, field, secret):
    """Given a name and a secret, generate the key to store it with --
    which is a combination of the name, the field and a random string
    -- and store it in the keyring. Return the key it is stored with.

    """
    key = '%s|%s|%s' % (name, field, random_suffix())
    set_password(KEYRING_SYSTEM_NAME, key, secret)
    return key


def load_secret(name, field, key):
    try:
        # this is safe because neither of field or rand will have
        # pipes in.
        name_, field_, rand = key.rsplit('|', 2)
    except ValueError:
        print('Invalid key format for {name}.{field}'.format(name=name, field=field))
        return ''

    if (field_ != field):
        print('Invalid key format for {name}.{field}'.format(name=name, field=field))
        return ''

    secret = get_password(KEYRING_SYSTEM_NAME, key)
    if secret is None:
        print('No secret found for {name}.{field}'.format(name=name, field=field))
        return ''

    return secret


def encode_connection(connection):
    opts = connection.__dict__

    for sf in SECRET_FIELDS:
        opts[sf] = store_new_secret(connection.name, sf, opts[sf])
    return Connection(**opts)

def decode_connection(connection):
    opts = connection.__dict__

    for sf in SECRET_FIELDS:
        opts[sf] = load_secret(connection.name, sf, opts[sf])
    return Connection(**opts)
