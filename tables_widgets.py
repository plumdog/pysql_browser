from PySide import QtCore, QtGui


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
        return [('Set Default Database', self.setDefaultDatabase),
                ('Reload Tables', self.reloadTables)]

    def reloadTables(self):
        self.treeWidget().window().set_tables(self.db_name)

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
        db_item = self.db_items.get(db)
        if db_item:
            db_item.takeChildren()
            for t in tables:
                t_item = TablesWidgetItemTable(db_item, t)
