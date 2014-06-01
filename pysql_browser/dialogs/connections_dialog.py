from collections import OrderedDict

from PySide import QtGui, QtCore

from ..connections import Connection
from ..settings_saver import save, load


class ConnectionsDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(ConnectionsDialog, self).__init__(parent)
        self.setWindowTitle('Connections')
        self.connections_list = ConnectionsList()

        self.form = ConnectionForm()
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.connections_list)
        layout.addLayout(self.form)

        self.setLayout(layout)
        

class ConnectionsList(QtGui.QListWidget):
    def __init__(self, parent=None):
        super(ConnectionsList, self).__init__(parent)
        self.load_items()
        self.currentRowChanged.connect(self.item_changed)

    def item_changed(self, current):
        try:
            connection = self.connections[current]
        except IndexError:
            pass
        else:
            self.parent().form.load_connection(current, connection)

    def set_connection(self, row_num, connection):
        if row_num is None:
            self.connections.append(connection)
        else:
            self.connections[row_num] = connection
        save('connections', self.connections)
        self.load_items()

        return self.connections.index(connection)

    def del_connection(self, row_num):
        del self.connections[row_num]
        save('connections', self.connections)
        self.load_items()

    def load_items(self):
        self.connections = load('connections', [])
        self.clear()
        self.addItems([c.name for c in self.connections])


class ConnectionForm(QtGui.QFormLayout):
    def __init__(self, parent=None):
        super(ConnectionForm, self).__init__(parent)
        self.fields = OrderedDict([
            ('name', 'Name'),
            ('local_port', 'Local Port'),
            ('remote_user', 'Remote User'),
            ('remote_server', 'Remote Server'),
            ('remote_port', 'Remote Port'),
            ('remote_password', 'Remote Password'),
            ('mysql_username', 'Mysql User'),
            ('mysql_password', 'Mysql Password'),
        ])

        for key, name in self.fields.items():
            f = self._add_text_edit(name)
            f.textChanged.connect(self.text_changed)
            setattr(self, key, f)

        self.save_button = QtGui.QPushButton('Save')
        self.save_button.clicked.connect(self.save_form)
        self.reset_button = QtGui.QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_form)
        self.new_button = QtGui.QPushButton('New')
        self.new_button.clicked.connect(self.new_form)
        self.delete_button = QtGui.QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_connection)

        self.row_num = None

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.delete_button)

        self.addRow(buttons_layout)

    def text_changed(self, text):
        self.set_changed(True)

    def save_form(self):
        opts = {}
        for f in self.fields.keys():
            opts[f] = getattr(self, f).text()
        try:
            opts['local_port'] = int(opts['local_port'])
        except ValueError:
            opts['local_port'] = 3307

        try:
            opts['remote_port'] = int(opts['remote_port'])
        except ValueError:
            opts['remote_port'] = 3306

        connection = Connection(**opts)
        self.row_num = self.connections_dialog().connections_list.set_connection(self.row_num, connection)
        self.set_changed(False)

    def reset_form(self):
        connections = self.connections_dialog().connections_list.connections
        try:
            connection = connections[self.row_num]
        except IndexError:
            return

        self.load_connection(self.row_num, connection)

    def new_form(self):
        connection = Connection(*([''] * len(self.fields)))
        self.load_connection(None, None)
        self.set_changed(False)

    def delete_connection(self):
        self.connections_dialog().connections_list.del_connection(self.row_num)
        self.new_form()

    def load_connection(self, row_num, connection):
        self.row_num = row_num
        for f in self.fields.keys():
            if connection:
                val = getattr(connection, f)
            else:
                val = ''
            getattr(self, f).setText(str(val))
        self.set_changed(False)

    def set_changed(self, val):
        self.save_button.setEnabled(val)
        self.reset_button.setEnabled(val)
        self.changed = val
        

    def _add_text_edit(self, label_text, input_text=''):
        label = QtGui.QLabel(label_text)
        text_edit = QtGui.QLineEdit()
        text_edit.setText(input_text)
        self.addRow(label, text_edit)
        return text_edit
    
    def connections_dialog(self):
        return self.parent().parent()
