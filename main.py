import sys

from code.visualisation.model import Model
from PyQt5 import QtWidgets


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Model()
    window.show()
    app.exec_()

main()
