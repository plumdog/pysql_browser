from PySide import QtCore, QtGui
from pysql_browser import MainWindow
import sys

def main():
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
