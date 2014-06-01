from functools import partial
from collections import namedtuple

from PySide import QtCore, QtGui

from .mysql_connection import TunnelledMySQL, QueryError, OperationalError
from .tables_widgets import TablesWidget
from .tab_widgets import Tabs, Tab
from . import app_config
from .mysql_utils import escape
from .sql_loader import SQLLoader
from .dialogs.connections_dialog import ConnectionsDialog
from .connections import Connection
from .connections_saver import load


TEST = False


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.setWindowTitle(app_config.window_title)
        self.setWindowIcon(QtGui.QIcon('python.png'))

        self.db = None
        self.tables_widget = TablesWidget(self)

        self.last_query_table = None
        self.last_query_db = None
        self.last_query_table_columns = None
        self.last_query_fks = None
        self.last_query_fks_in = None
        self.tab_count = 0

        self.default_database = None
        self.progress_bar = None
        self.connections = []
        self.connections_menu = None
        self.create_menus()

        self.main_splitter = QtGui.QSplitter()
        self.tabs_widget = Tabs(self)
        self.tabs_widget.setTabsClosable(True)
        
        self.main_splitter.addWidget(self.tables_widget)
        self.main_splitter.addWidget(self.tabs_widget)
        self.main_splitter.setSizes((1, 1))
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(app_config.h_split_handle)
        self.setCentralWidget(self.main_splitter)

        self.statusBar().showMessage("Startup Completed")

    def new_tab(self):
        ind = self.tabs_widget.currentIndex() + 1
        self.tab_count += 1
        set_ind = self.tabs_widget.insertTab(ind, Tab(self), 'SQL ' + str(self.tab_count))
        self.tabs_widget.setCurrentIndex(set_ind)

    def create_menus(self):
        file_menu = self.menuBar().addMenu('&File')
        action = QtGui.QAction('New &Tab', self)
        action.triggered.connect(self.new_tab)
        file_menu.addAction(action)
        self.connections_menu = self.menuBar().addMenu('&Connections')
        self.populate_connections_menu()

    def populate_connections_menu(self):
        self.connections_menu.clear()
        self.connections = load()
        if self.connections:
            for connection in self.connections:
                action = QtGui.QAction(connection.name, self)
                action.triggered.connect(partial(self.set_db_server, connection))
                self.connections_menu.addAction(action)
        else:
            action = QtGui.QAction('No Connections Configured', self)
            action.setEnabled(False)
            self.connections_menu.addAction(action)

        self.connections_menu.addSeparator()
        edit_connections_action = QtGui.QAction('Edit Connections', self)
        edit_connections_action.triggered.connect(self.connections_dialog)
        self.connections_menu.addAction(edit_connections_action)

    def connections_dialog(self):
        servers_dialog = ConnectionsDialog()
        servers_dialog.show()
        servers_dialog.exec_()
        self.populate_connections_menu()

    def set_db_server(self, connection):
        self._set_db_server_first(connection)

        self.statusBar().showMessage('Loading ' + connection.name)
        self.repaint()
        self.thread = ConnectThread(self, **connection.__dict__)
        self.thread.finished.connect(self._set_db_server_second)
        self.thread.start()

    def _set_db_server_first(self, connection):
        if self.db and self.db.enter_ok:
            self.db.close()

        self.tabs_widget.clear()
        self.repaint()

    def _set_db_server_second(self):
        if self.thread.error:
            if isinstance(self.thread.error, EOFError):
                message = 'SSH Tunnel connection failed.'
            elif isinstance(self.thread.error, OperationalError):
                code, message = self.thread.error.args

            self.statusBar().showMessage('Error: ' + message)
        else:
            self.db = self.thread.db
            self.load_dbs()
            self.statusBar().showMessage('Loaded')
        
    def load_dbs(self):
        self.tables_widget.clear()

        dbs = self.get_databases()
        self.tables_widget.dbs(dbs)

        _dbs = [d for d in dbs if ' ' not in d]
        if _dbs and False:
            num_dbs = len(_dbs)
            pc = app_config.progress_jump
            full = 100
            each = (full - pc) / num_dbs

    def get_databases(self):
        cmd = SQLLoader.show_databases
        keys, results = self.execute_sql(cmd)
        return [d[0] for d in results]

    def get_tables(self, db):
        cmd = SQLLoader.show_tables.format(db=db)
        keys, results = self.execute_sql(cmd)
        return [t[0] for t in results]

    def set_tables(self, db):
        self.tables_widget.tables(db, self.get_tables(db))

    def _db_prefix(self, db):
        if self.default_database == db:
            return ''
        else:
            return db + '.'

    def get_table_info(self, db, table_name):
        db_prefix = self._db_prefix(db)
        cols_cmd = SQLLoader.show_columns.format(db_prefix=db_prefix, table_name=table_name)
        col_keys, cols = self.execute_sql(cols_cmd)

        info_cmd = SQLLoader.table_status.format(db=db, table_name=table_name)
        keys, info = self.execute_sql(info_cmd)
        info_list = zip(list(keys), list(info[0]))

        return (col_keys, list(cols)), info_list

    def select_star(self, db, table_name, wheres=[], get_sql_only=False):
        db_prefix = self._db_prefix(db)
        sql = SQLLoader.select_star.format(
            db_prefix=db_prefix, table_name=table_name)
        
        if wheres:
            wheres_sql = ' AND '.join(wheres)
            sql += ' WHERE ' + wheres_sql

        sql += ';'

        if get_sql_only:
            return sql
            
        cols_sql = SQLLoader.show_columns.format(
            db_prefix=db_prefix, table_name=table_name)
        fks_sql = SQLLoader.fks.format(
            tab=escape(table_name, quote=True),
            db=escape(db, quote=True))
        fks_in_sql = SQLLoader.fks_in.format(
            tab=escape(table_name, quote=True),
            db=escape(db, quote=True))
        
        _, self.last_query_table_columns = self.execute_sql(cols_sql)
        _, self.last_query_fks = self.execute_sql(fks_sql)
        _, self.last_query_fks_in = self.execute_sql(fks_in_sql)
        self.current_tab_widget().query_widget.execute_sql_and_show(sql, set_widget_text=True)
        self.last_query_table = table_name
        self.last_query_db = db


    def current_tab_widget(self):
        if self.tabs_widget.count() == 0:
            return self.new_tab_widget()
        else:
            return self.new_tab_widget()

    def new_tab_widget(self):
        curr = self.tabs_widget.currentWidget()
        if curr and curr.is_empty():
            return curr
        else:
            self.new_tab()
            return self.current_tab_widget()

    def execute_sql(self, sql, notify=True, sql_params=[], limit=None):
        if self.db is None:
            if notify:
                print('No database loaded')
            return [], []

        if self.db.connection is None:
            if notify:
                print('No connection to database established')
            return [], []

        try:
            if self.default_database:
                self.db.connection.cursor().execute(SQLLoader.use.format(db=self.default_database))
            cursor = self.db.connection.cursor()
            cursor.execute(sql, *sql_params)
                
        except QueryError as e:
            if notify:
                print('Error:' + str(e))
        except OperationalError as e:
            if notify:
                print('Error:' + str(e))
        except Exception:
            raise
        else:
            if notify:
                print('Success')

            if limit is None:
                result_rows = cursor.fetchall()
            else:
                result_rows = cursor.fetchmany(limit)

            if result_rows is None:
                return None, None
            
            if not cursor.description:
                # then there are no columns in the return set. Return empties
                if notify:
                    print('No columns in returned set')
                return [], []
            else:
                ColKey = namedtuple(
                    'ColKey',
                    'name type_code display_size internal_size precision scale null_ok')
                cols = [ColKey(*d) for d in cursor.description]
                Row = namedtuple('Row', [col.name for col in cols])
                rows = [Row(*r) for r in result_rows]
                return (cols, rows)

class ConnectThread(QtCore.QThread):
    def __init__(self, parent=None, name='', **connection_config):
        super().__init__(parent)
        self.db = None
        self.connection_config = connection_config
        self.error = None

    def run(self):
        print('start')
        self.db = TunnelledMySQL(**self.connection_config)
        try:
            self.db.__enter__()
        except Exception as e:
            self.error = e
        print('done')
