from PySide import QtCore, QtGui

from mysql_connection import TunnelledMySQL, QueryError, TransactionError
from results_widgets import ResultsWidget
from query_widgets import QueryWidget
from tables_widgets import TablesWidget
from config import config
from mysql_utils import escape

TEST = False


class MainWindow(QtGui.QMainWindow):
    def __init__(self, db, parent=None, **kwargs):
        super().__init__(parent)
        self.db = db
        self.query_widget = QueryWidget(self)
        self.results_widget = ResultsWidget(self)
        self.tables_widget = TablesWidget(self)
        self.last_query_table = None
        self.last_query_db = None
        self.last_query_table_columns = None
        self.last_query_fks = None
        self.last_query_fks_in = None

        self.default_database = None

        dbs = self.get_databases()
        self.tables_widget.dbs(dbs)
        for d in dbs:
            if ' ' not in d:
                self.set_tables(d)

        self.main_splitter = QtGui.QSplitter()
        query_and_results_splitter = QtGui.QSplitter(self)
        query_and_results_splitter.setOrientation(QtCore.Qt.Vertical) 
        query_and_results_splitter.addWidget(self.query_widget)
        query_and_results_splitter.addWidget(self.results_widget)
        query_and_results_splitter.setStretchFactor(0, 2)
        query_and_results_splitter.setStretchFactor(1, 3)
        query_and_results_splitter.setChildrenCollapsible(False)
        query_and_results_splitter.setHandleWidth(3)
        
        self.main_splitter.addWidget(self.tables_widget)
        self.main_splitter.addWidget(query_and_results_splitter)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(3)
        self.setCentralWidget(self.main_splitter)

    def get_databases(self):
        if TEST:
            return ['db1', 'db2']
        cmd = 'SHOW DATABASES;'
        keys, results = self.execute_sql(cmd)
        return [d[0] for d in results]

    def get_tables(self, db):
        if TEST:
            return ['t1', 't2']
        cmd = 'SHOW TABLES FROM ' + db + ';'
        keys, results = self.execute_sql(cmd)
        return [t[0] for t in results]

    def set_tables(self, db):
        self.tables_widget.tables(db, self.get_tables(db))

    def select_star(self, db, table_name, wheres=[], get_sql_only=False):
        if self.default_database == db:
            db_prefix = ''
        else:
            db_prefix = db + '.'
        sql = 'SELECT * FROM {db_prefix}{table_name}'.format(
            db_prefix=db_prefix, table_name=table_name)
        
        if wheres:
            wheres_sql = ' AND '.join(wheres)
            sql += ' WHERE ' + wheres_sql

        sql += ';'

        if get_sql_only:
            return sql
            
        cols_sql = 'SHOW COLUMNS FROM {db_prefix}{table_name};'.format(
            db_prefix=db_prefix, table_name=table_name)
        fks_sql = 'SELECT * FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME = {tab} AND TABLE_SCHEMA = {db} AND REFERENCED_TABLE_NAME IS NOT NULL'.format(
            tab=escape(table_name, quote=True),
            db=escape(db, quote=True))
        fks_in_sql = 'SELECT * FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME IS NOT NULL AND TABLE_SCHEMA = {db} AND REFERENCED_TABLE_NAME = {tab}'.format(
            tab=escape(table_name, quote=True),
            db=escape(db, quote=True))
        
        if TEST:
            print(sql)
            print(cols_sql)
            print(fks_sql)
            print(fks_in_sql)
        else:
            _, self.last_query_table_columns = self.execute_sql(cols_sql)
            _, self.last_query_fks = self.execute_sql(fks_sql)
            _, self.last_query_fks_in = self.execute_sql(fks_in_sql)
            self.query_widget.execute_sql_and_show(sql, set_widget_text=True)
        self.last_query_table = table_name
        self.last_query_db = db

    def execute_sql(self, sql, notify=True, sql_params=[], limit=None):
        try:
            if self.default_database:
                self.db.connection.execute('USE ' + self.default_database)
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


def main(db=None):
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWindow(db=db)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    if TEST:
        main()
    else:
        with TunnelledMySQL(**config) as db:
            main(db)
