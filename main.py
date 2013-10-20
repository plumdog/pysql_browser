import sys
from pprint import pprint
from functools import partial

from PySide import QtCore, QtGui

from mysql_connection import TunnelledMySQL, QueryError
from sql_highlighter import SQLHighlighter
from config import config

LIMIT = 100


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
                self.tables_widget.tables(d, self.get_tables(d))

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
        return [d[0] for d in list(self.execute_sql(cmd).fetchall())]

    def get_tables(self, db):
        if TEST:
            return ['t1', 't2']
        cmd = 'SHOW TABLES FROM ' + db + ';'
        return [t[0] for t in list(self.execute_sql(cmd).fetchall())]

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
            tab=self.escape_for_sql(table_name, quote=True),
            db=self.escape_for_sql(db, quote=True))
        fks_in_sql = 'SELECT * FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME IS NOT NULL AND TABLE_SCHEMA = {db} AND REFERENCED_TABLE_NAME = {tab}'.format(
            tab=self.escape_for_sql(table_name, quote=True),
            db=self.escape_for_sql(db, quote=True))
        
        if TEST:
            print(sql)
            print(cols_sql)
            print(fks_sql)
            print(fks_in_sql)
        else:
            self.last_query_table_columns = self.execute_sql(cols_sql)
            self.last_query_fks = self.execute_sql(fks_sql)
            self.last_query_fks_in = self.execute_sql(fks_in_sql)
            print(self.last_query_fks_in)
            self.query_widget.execute_sql(sql, set_widget_text=True)
        self.last_query_table = table_name
        self.last_query_db = db

    def escape_for_sql(self, string, quote=False):
        string = string.replace('\n', '\\n').replace('\r', '\\r').replace('\\', '\\\\')
        string = string.replace("'", "\'").replace('"', '\"')
        string = string.replace('\x00', '\\x00').replace('\x1a', '\\x1a')
        if quote:
            return '"' + string + '"'
        else:
            return string

    def execute_sql(self, sql, notify=True, sql_params=[]):
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
            return results


class QueryWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.execute_button = QtGui.QPushButton("Execute", self)
        self.query_text_widget = QueryTextWidget(self)

        self.execute_button.clicked.connect(self.execute_sql_from_input)

        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.execute_button)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.query_text_widget)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def execute_sql_from_input(self):
        self.execute_sql(self.sql())
        self.window().last_query_table_columns = None
        self.window().last_query_table = None

    def execute_sql(self, sql, set_widget_text=False):
        result = None
        main_window = self.window()

        if set_widget_text:
            self.query_text_widget.setText(sql)

        print(sql)
        if TEST:
            return
        
        if db.enter_ok:
            result = main_window.execute_sql(sql)

        print('Set Table')
        if result:
            main_window.results_widget.results_widget_table.show_result(
                result,
                self.window().last_query_table_columns,
                self.window().last_query_fks,
                self.window().last_query_fks_in)
            print('Set Table Done')
        else:
            print('no result to display')

    def sql(self):
        return self.query_text_widget.toPlainText()


class QueryTextWidget(QtGui.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        font = QtGui.QFont()
        font.setFamily('FreeMono')
        self.setFont(font)

        self.highlighter = SQLHighlighter(self.document())


class ResultsWidgetTableItem(QtGui.QTableWidgetItem):
    #DisplayTextRole = QtCore.Qt.UserRole
    #EditTextRole = QtCore.Qt.UserRole + 1
    #TextLimit = 100
    
    def __init__(self, data):
        #text = str(data)
        #if len(text) > self.TextLimit:
        #     text = text[:self.TextLimit] + '...'
        super().__init__(str(data))
        # self.edit_text = str(data)


class ResultsWidgetTableItemDelegate(QtGui.QAbstractItemDelegate):
    def editorEvent(self, event, model, option, index):
        print(event, model, option, index)


class ResultsWidgetTable(QtGui.QTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.changed_items = {}
        self.items_loaded = False
        self.itemChanged.connect(self.on_change)
        self.row_number_to_pk = {}
        self.col_number_to_field = {}
        self.pk_col_name = None
        self.fks = {}
        self.fks_in = []

    
    def show_result(self, result, columns=None, fks=None, fks_in=None):
        keys = result.keys()
        self.setColumnCount(len(keys))
        self.setRowCount(min(result.rowcount, LIMIT))

        for col, key_name in enumerate(keys):
            key_header = QtGui.QTableWidgetItem(key_name)
            key_header.setTextAlignment(QtCore.Qt.AlignLeft)
            self.setHorizontalHeaderItem(col, key_header)
            self.col_number_to_field[col] = key_name

        self.setVerticalHeaderLabels([str(i) for i in (range(1, result.rowcount))])

        self.fks = {}
        if fks:
            for fk in fks:
                self.fks[fk.COLUMN_NAME] = (
                    fk.REFERENCED_TABLE_SCHEMA, fk.REFERENCED_TABLE_NAME, fk.REFERENCED_COLUMN_NAME)
        self.fks_in = []
        print(fks_in)
        if fks_in:
            for fk in fks_in:
                self.fks_in.append(
                    (fk.REFERENCED_COLUMN_NAME, fk.TABLE_SCHEMA,
                     fk.TABLE_NAME, fk.COLUMN_NAME))

        rows = result.fetchmany(LIMIT)
        primary_col_num = None
        if columns:
            for col_num, col in enumerate(columns):
                print(col.keys())
                print(col)
                print(col.Key)
                if col.Key == 'PRI':
                    primary_col_num = col_num
                    self.pk_col_name = col.Field
                    break

        for row_num, row in enumerate(rows):
            for col_num, data in enumerate(row):
                self.setItem(row_num, col_num, ResultsWidgetTableItem(str(data)))
                if primary_col_num == col_num:
                    self.row_number_to_pk[row_num] = data

        header = self.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHorizontalHeader(header)
        self.items_loaded = True
        self.changed_items = {}

        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        # print('done show')

    def on_change(self, item):
        if self.items_loaded:
            pos = (item.column(), item.row())
            self.changed_items[pos] = item.text()

    def fk_out(self, item, fk, get_sql_only=False):
        print('fk_out', fk)
        f_db, f_tab, f_col = fk
        return self.window().select_star(f_db, f_tab, [f_col + ' = ' + self.window().escape_for_sql(item.text(), quote=True)], get_sql_only)

    def fk_in(self, item, fk, get_sql_only=False):
        print('fk_in', fk)
        ref_col, db, tab, col = fk
        return self.window().select_star(db, tab, [col + ' = ' + self.window().escape_for_sql(item.text(), quote=True)], get_sql_only)

    def contextMenuEvent(self, event):
        pos = event.globalPos()
        item = self.currentItem()
        menu = QtGui.QMenu()
        field = self.col_number_to_field.get(item.column())
        fk = self.fks.get(field)
        if fk:
            action = QtGui.QAction(self.fk_out(item, fk, get_sql_only=True), self)
            action.triggered.connect(partial(self.fk_out, item, fk))
            menu.addAction(action)

        for fk in [fk for fk in self.fks_in if fk[0] == field]:
            action = QtGui.QAction(self.fk_in(item, fk, get_sql_only=True), self)
            action.triggered.connect(partial(self.fk_in, item, fk))
            menu.addAction(action)

        menu.exec_(pos)


class ResultsWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_widget_table = ResultsWidgetTable(self)
        self.commit_button = QtGui.QPushButton("Commit", self)

        self.commit_button.clicked.connect(self.commit_changes)

        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.commit_button)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.results_widget_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def commit_changes(self):
        for (col_num, row_num), new_text in self.results_widget_table.changed_items.items():
            pk = self.results_widget_table.row_number_to_pk.get(row_num)
            field = self.results_widget_table.col_number_to_field.get(col_num)

            sql = 'UPDATE {db}.{table} SET {field} = {new_text} WHERE {pk_field} = {pk}'.format(
                db=self.window().last_query_db,
                table=self.window().last_query_table,
                field=field,
                pk_field=self.results_widget_table.pk_col_name,
                new_text=self.window().escape_for_sql(new_text, quote=True),
                pk=pk)
            self.window().execute_sql(sql, new_text)
        self.results_widget_table.changed_items = {}


class TablesWidgetItem(QtGui.QTreeWidgetItem):
    def contextMenuEvent(self, pos):
        menu = QtGui.QMenu()
        for name, func in self.contextMenuActions():
            action = QtGui.QAction(name, self.treeWidget())
            action.triggered.connect(func)
            menu.addAction(action)
        menu.exec_(pos)

    def contextMenuActions(self):
        raise NotImplementedError('Must define contextMenuActions method')
        

class TablesWidgetItemDatabase(TablesWidgetItem):
    def __init__(self, parent=None, db_name=None):
        super().__init__(parent)
        self.db_name = db_name
        self.setText(0, db_name)

    def contextMenuActions(self):
        return [('Set Default Database', self.setDefaultDatabase)]

    def setDefaultDatabase(self):
        self.treeWidget().window().default_database = self.db_name
        for index in range(self.treeWidget().topLevelItemCount()):
            item = self.treeWidget().topLevelItem(index)
            if item:
                item.unbold()
        self.bold()

    def bold(self):
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(0, font)

    def unbold(self):
        font = QtGui.QFont()
        font.setBold(False)
        self.setFont(0, font)


class TablesWidgetItemTable(TablesWidgetItem):
    def __init__(self, parent=None, table_name=None):
        super().__init__(parent)
        self.table_name = table_name
        self.setText(0, table_name)

    def contextMenuActions(self):
        return [('Select All', self.select_star)]

    def select_star(self):
        self.treeWidget().window().select_star(self.parent().db_name, self.table_name)


class TablesWidget(QtGui.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dbs_list = []
        self.db_items = {}
        self.header().hide()

    def contextMenuEvent(self, event):
        item = self.currentItem()
        pos = event.globalPos()
        if isinstance(item, TablesWidgetItem):
            item.contextMenuEvent(pos)
    
    def dbs(self, dbs):
        self.dbs_list = dbs
        for db in dbs:
            db_item = TablesWidgetItemDatabase(self, db)
            self.db_items[db] = db_item

    def tables(self, db, tables):
        for t in tables:
            t_item = TablesWidgetItemTable(self.db_items[db], t)
            
def main(db=None):
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
