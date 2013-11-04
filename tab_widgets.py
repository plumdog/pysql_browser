from PySide import QtCore, QtGui

from query_widgets import QueryWidget
from results_widgets import ResultsWidget
import app_config

class Tabs(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tabBar().tabCloseRequested.connect(self.close_tab)

    def close_tab(self, index):
        self.removeTab(index)


class Tab(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.query_widget = QueryWidget(self)
        self.results_widget = ResultsWidget(self)

        query_and_results_splitter = QtGui.QSplitter(self)
        query_and_results_splitter.setOrientation(QtCore.Qt.Vertical) 
        query_and_results_splitter.addWidget(self.query_widget)
        query_and_results_splitter.addWidget(self.results_widget)
        #query_and_results_splitter.setStretchFactor(0, app_config.v_split_1)
        #query_and_results_splitter.setStretchFactor(1, app_config.v_split_2)
        query_and_results_splitter.setChildrenCollapsible(False)
        query_and_results_splitter.setHandleWidth(app_config.v_split_handle)

        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(query_and_results_splitter)
        self.setLayout(layout)

    def is_empty(self):
        return ((self.results_widget.results_widget_table.rowCount() == 0)
                and (self.results_widget.results_widget_table.columnCount() == 0)
                and (self.query_widget.sql() == ''))
