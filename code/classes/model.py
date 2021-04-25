from PyQt5 import QtWidgets
from ..visualisation.grid_window import Grid_Window


class Model(QtWidgets.QWidget):
    """The PyQT5 widget that contains all the contents of the model.

    It contains two windows: the visualisation of the grid and a menu
    to adjust the parameters of the model.
    """
    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        self.setWindowTitle("Grid-Based Movement Model")

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(Grid_Window(), 1)
        layout.addWidget(QtWidgets.QPushButton('Run'))

        self.setLayout(layout)
