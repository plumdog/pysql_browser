pysql_browser
=============

GUI for connection to and management of remote MySQL servers.

At present, there is no internal management of connection
credentials. You have to create a file called db_config.py and enter a dict:

```python
config = {
    'Server Name': (
        'Server Name',
        {'local_port': 3307,
	 'remote_user': 'root',
         'remote_server': 'host.com',
         'remote_port': 3306,
         'remote_password': '',
         'mysql_username': 'root',
         'mysql_password': ''
         }),
    # etc
}
```

The values give above are the defaults, so you only need to add values
where they differ.
