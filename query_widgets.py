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

        if result:
            main_window.results_widget.results_widget_table.show_result(
                result,
                keys,
                list(self.window().last_query_table_columns),
                list(self.window().last_query_fks),
                list(self.window().last_query_fks_in))
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
