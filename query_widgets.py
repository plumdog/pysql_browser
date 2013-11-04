from PySide import QtCore, QtGui

from sql_highlighter import SQLHighlighter
from results_widgets import LIMIT


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
        self.execute_sql_and_show(self.sql())
        self.window().last_query_table_columns = None
        self.window().last_query_table = None

    def execute_sql_and_show(self, sql, set_widget_text=False, limit=LIMIT):
        result = None
        main_window = self.window()

        if set_widget_text:
            self.query_text_widget.setText(sql)

        print(sql)
        
        if main_window.db.enter_ok:
            keys, result = main_window.execute_sql(sql, limit=limit)

        last_query_table_columns = self.window().last_query_table_columns
        last_query_fks = self.window().last_query_fks
        last_query_fks_in = self.window().last_query_fks_in

        if last_query_table_columns is not None:
            last_query_table_columns = list(last_query_table_columns)

        if last_query_fks is not None:
            last_query_fks = list(last_query_fks)

        if last_query_fks_in is not None:
            last_query_fks_in = list(last_query_fks_in)

        if result:
            self.results_widget().results_widget_table.show_result(
                result,
                keys,
                last_query_table_columns,
                last_query_fks,
                last_query_fks_in)
        else:
            self.results_widget().results_widget_table.clear()
            print('no result to display')

    def sql(self):
        return self.query_text_widget.toPlainText()

    def results_widget(self):
        return self.parent().parent().results_widget


class QueryTextWidget(QtGui.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        font = QtGui.QFont()
        font.setFamily('FreeMono')
        self.setFont(font)

        self.highlighter = SQLHighlighter(self.document())
