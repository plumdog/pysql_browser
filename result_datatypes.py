from mysql_utils import escape


def field_type_to_datatype(field_type):
    if field_type.lower().startswith('int'):
        return ResultInteger
    elif field_type.lower().startswith('decimal'):
        return ResultFloat
    else:
        return ResultString


class ResultDatatype(object):
    def __init__(self, value=None):
        self.value = value

    def from_string(self, string):
        raise NotImplementedError('Must implement from_string method')

    def where_sql(self, col):
        if self.value is None:
            return col + ' IS NULL'
        else:
            return col + ' = ' + escape(self.value, quote=True)

    def set_to_null(self):
        self.value = None

    def get_text(self):
        if self.value is None:
            return 'NULL'
        else:
            return str(self.value)

class ResultString(ResultDatatype):
    def from_string(self, string):
        self.value = string
        return True

class ResultInteger(ResultDatatype):
    def from_string(self, string):
        try:
            self.value = int(string)
        except ValueError:
            return False
        else:
            return True

    def where_sql(self, col):
        if self.value is not None:
            return col + ' = ' + str(self.value)

class ResultFloat(ResultInteger):
    def from_string(self, string):
        try:
            self.value = float(string)
        except ValueError:
            return False
        else:
            return True

    def where_sql(self, col):
        if self.value is not None:
            return col + ' = %f' % self.value
