from functools import partial
from pprint import pprint

from PySide import QtCore, QtGui

from result_datatypes import ResultString, ResultInteger, field_type_to_datatype
from mysql_utils import escape

FKS_IN_MENU_LIMIT = 20
LIMITS = [20, 50, 100, 200, 500]

class ResultsWidgetTableItem(QtGui.QTableWidgetItem):
    def __init__(self, data, datatype):
        self._datatype = datatype
        self._data = datatype(data)
        
        super().__init__(self._data.get_text())

    def getData(self):
        return self._data

    def set_from_string(self):
        return self._data.from_string(self.text())

    def set_to_null(self):
        self._data.set_to_null()

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

    def disable_editting(self):
        self.setEditTriggers(self.NoEditTriggers)

    def enable_editting(self):
        self.setEditTriggers(self.AnyKeyPressed | self.EditKeyPressed | self.DoubleClicked)
    
    def show_result(self, result, keys, columns=None, fks=None, fks_in=None):
        self.setColumnCount(len(keys))
        self.setRowCount(min(len(result), self.parent().fetch_limit))

        for col, key_name in enumerate(keys):
            key_header = QtGui.QTableWidgetItem(key_name.name)
            key_header.setTextAlignment(QtCore.Qt.AlignLeft)
            self.setHorizontalHeaderItem(col, key_header)
            self.col_number_to_field[col] = key_name

        self.setVerticalHeaderLabels([str(i) for i in (range(1, len(result)))])

        self.fks = {}
        if fks:
            for fk in fks:
                self.fks[fk.COLUMN_NAME] = (
                    fk.REFERENCED_TABLE_SCHEMA, fk.REFERENCED_TABLE_NAME, fk.REFERENCED_COLUMN_NAME)
        self.fks_in = []
        if fks_in:
            for fk in fks_in:
                self.fks_in.append(
                    (fk.REFERENCED_COLUMN_NAME, fk.TABLE_SCHEMA,
                     fk.TABLE_NAME, fk.COLUMN_NAME))

        rows = result
        primary_col_num = None
        if columns:
            self.enable_editting()
            for col_num, col in enumerate(columns):
                if col.Key == 'PRI':
                    primary_col_num = col_num
                    self.pk_col_name = col.Field
                    break
        else:
            self.disable_editting()
        
        for row_num, row in enumerate(rows):
            for col_num, data in enumerate(row):
                if columns is not None:
                    datatype = field_type_to_datatype(columns[col_num].Type)
                else:
                    datatype = ResultString
                self.setItem(row_num, col_num, ResultsWidgetTableItem(data, datatype))
                if primary_col_num == col_num:
                    self.row_number_to_pk[row_num] = data

        header = self.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setHorizontalHeader(header)
        self.items_loaded = True
        self.changed_items = {}

        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

    def on_change(self, item):
        if self.items_loaded:
            pos = (item.column(), item.row())
            self.changed_items[pos] = item.text()
            
            if not item.set_from_string():
                item.setText('NULL')
                

    def fk_out(self, item, fk, get_sql_only=False):
        f_db, f_tab, f_col = fk
        
        where = self.where_str(f_col, item)
        return self.window().select_star(f_db, f_tab, [where], get_sql_only)

    def fk_in(self, item, fk, get_sql_only=False):
        ref_col, db, tab, col = fk
        where = self.where_str(col, item)
        return self.window().select_star(db, tab, [where], get_sql_only)

    def where_str(self, col, item):
        return item.getData().where_sql(col)

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

        fk_actions = {}
        for fk in [fk for fk in self.fks_in if fk[0] == field]:
            action = QtGui.QAction(self.fk_in(item, fk, get_sql_only=True), self)
            action.triggered.connect(partial(self.fk_in, item, fk))
            tab_initial = fk[2][0]
            fk_actions[tab_initial] = fk_actions.get(tab_initial, []) + [action]

        total_actions = sum(len(actions_list) for actions_list in fk_actions.values())

        submenus = (total_actions > FKS_IN_MENU_LIMIT)
        for initial, action_list in sorted(fk_actions.items()):
            if submenus:
                submenu = menu.addMenu(initial.upper())
                for action in action_list:
                    submenu.addAction(action)
            else:
                for action in action_list:
                    menu.addAction(action)

        menu.exec_(pos)


class ResultsWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_widget_table = ResultsWidgetTable(self)
        self.commit_button = QtGui.QPushButton("Commit", self)
        self.fetch_limit_options = QtGui.QComboBox(self)
        self.fetch_limit_options.addItems([str(lim) for lim in LIMITS])

        start_index = 2
        self.fetch_limit = LIMITS[2]
        self.fetch_limit_options.setCurrentIndex(start_index)

        self.commit_button.clicked.connect(self.commit_changes)
        self.fetch_limit_options.currentIndexChanged.connect(self.set_limit)

        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.fetch_limit_options)
        button_layout.addWidget(self.commit_button)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.results_widget_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def commit_changes(self):
        for (col_num, row_num), new_text in self.results_widget_table.changed_items.items():
            pk = self.results_widget_table.row_number_to_pk.get(row_num)
            field = self.results_widget_table.col_number_to_field.get(col_num).name

            sql = 'UPDATE {db}.{table} SET {field} = {new_text} WHERE {pk_field} = {pk}'.format(
                db=self.window().last_query_db,
                table=self.window().last_query_table,
                field=field,
                pk_field=self.results_widget_table.pk_col_name,
                new_text=escape(new_text, quote=True),
                pk=pk)
            self.window().execute_sql(sql)
        self.results_widget_table.changed_items = {}

    def set_limit(self, index):
        print('set limit')
        self.fetch_limit = LIMITS[index]
            
