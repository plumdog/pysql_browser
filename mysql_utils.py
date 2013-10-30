def escape(string, quote=False):
    string = string.replace('\n', '\\n').replace('\r', '\\r').replace('\\', '\\\\')
    string = string.replace("'", "\'").replace('"', '\"')
    string = string.replace('\x00', '\\x00').replace('\x1a', '\\x1a')
    if quote:
        return '"' + string + '"'
    else:
        return string
