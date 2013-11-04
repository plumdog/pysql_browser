from functools import partial

from PySide import QtCore, QtGui

from mysql_connection import TunnelledMySQL, QueryError, TransactionError
from tables_widgets import TablesWidget
from tab_widgets import Tabs, Tab
from db_config import config
import app_config
from mysql_utils import escape
from sql_loader import SQLLoader

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

        servers_menu = self.menuBar().addMenu('&Servers')
        for server_key, (name, connection) in sorted(dict(config).items()):
            action = QtGui.QAction(name, self)
            action.triggered.connect(partial(self.set_db_server, server_key))
            servers_menu.addAction(action)

    def set_db_server(self, db_key):
        if self.db and self.db.enter_ok:
            self.db.close()

        self.tabs_widget.clear()
        self.repaint()

        name, connection_config = config[db_key]
        self.statusBar().showMessage('Loading ' + name)
        self.db = TunnelledMySQL(**connection_config)
        self.db.__enter__()
        self.load_dbs()
        self.statusBar().showMessage('Loaded ' + name)
        
    def load_dbs(self):
        self.tables_widget.clear()

        dbs = self.get_databases()
        self.tables_widget.dbs(dbs)

        _dbs = [d for d in dbs if ' ' not in d]

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

    def select_star(self, db, table_name, wheres=[], get_sql_only=False):
        if self.default_database == db:
            db_prefix = ''
        else:
            db_prefix = db + '.'
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
        try:
            if self.default_database:
                self.db.connection.execute(SQLLoader.use.format(db=self.default_database))
            results = self.db.connection.execute(sql, *sql_params)
                
        except QueryError as e:
            if notify:
                print('Error:' + str(e))
        except Exception:
            raise
        else:
            if notify:
                print('Success')

            try:
                if limit is None:
                    result_rows = results.fetchall()
                else:
                    result_rows = results.fetchmany(limit)
            except TransactionError as e:
                if notify:
                    print('No rows to get')
                return None
            else:
                return (results.keys(), result_rows)


def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
