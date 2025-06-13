#!/usr/bin/env python3
# PyQt5 GUI only version for cross-platform (Windows & Linux)
from ocrmypdfgui.gui_qt import MainWindow

def run():
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
