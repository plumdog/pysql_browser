from PySide import QtGui, QtCore

from .mysql_keywords import KEYWORDS

class SQLHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtCore.Qt.darkBlue)
        keyword_format.setFontWeight(QtGui.QFont.Bold)

        keyword_patterns = ["\\b" + keyword + "(\\b)(?!$)" for keyword in KEYWORDS]
        #keyword_patterns = ["\\b" + keyword + "\\b" for keyword in KEYWORDS]

        rules = []
        for pattern in keyword_patterns:
            regexp = QtCore.QRegExp(pattern)
            regexp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            rules.append((regexp, keyword_format))

        self.highlightingRules = rules


    def highlightBlock(self, text):
        for pattern, format_ in self.highlightingRules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format_)
                index = expression.indexIn(text, index + length)
