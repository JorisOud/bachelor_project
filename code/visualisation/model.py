import hexutil

from .grid import Grid
from PyQt5 import QtCore, QtGui, QtWidgets


class Model(QtWidgets.QMainWindow):
    """Contains the grid as a QGraphicsView for zoom and scroll functions.

    It allows for the grid to be zoomed in and out. This changes
    the boundaries of the widget which is accounted for by changing
    the maxima of the scroll bars.

    Attributes:
    |scene: Obj
    |view: Obj
    |grid: Grid

    Methods:
    |resizeEvent(event): instructs to update grid's dimensions when
    |   resized.
    |window_change(): changes the grid's visible window's dimensions.
    |zoom_in(): zooms in if allowed by adjusting the resolution of the
    |   hexagons.
    |zoom_out(): zooms out if allowed by adjusting the resolution of the
    |   hexagons.
    |set_scroll_area(): sets the maxima of the scrollbars to the maximum
    |   size of the grid.
    |set_view_to_center(Hex): sets the center of the view to the hexagon.
    """
    factor = 2

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.resize(800, 600)
        self.setWindowTitle("Grid-Based Movement Model")

        self.scene = QtWidgets.QGraphicsScene(self)
        self.view = QtWidgets.QGraphicsView(self.scene)

        self.grid = Grid()

        self.scene.addWidget(self.grid)
        self.setCentralWidget(self.view)

        # Connects scroll movements to update visible window of grid.
        self.view.verticalScrollBar().valueChanged.connect(
            lambda: self.window_change())
        self.view.horizontalScrollBar().valueChanged.connect(
            lambda: self.window_change())

        # Connects a keybind to the zoom in method.
        self.zoom_in_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence('Ctrl++'), self)
        self.zoom_in_shortcut.activated.connect(lambda: self.zoom_in())

        # Connects a keybind to the zoom out method.
        self.zoom_out_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence('Ctrl+-'), self)
        self.zoom_out_shortcut.activated.connect(lambda: self.zoom_out())

    def resizeEvent(self, event):
        """Instructs to update dimensions when window is resized."""
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.window_change()
        self.set_scroll_area()

    def window_change(self):
        """Changes the visible window's dimensions."""
        min_hor = self.view.horizontalScrollBar().value()
        min_ver = self.view.verticalScrollBar().value()

        view_rect = self.view.rect()
        left_side = min_hor
        bottom_side = min_ver

        self.grid.adjust_window(left_side,
                                bottom_side,
                                view_rect.width(),
                                view_rect.height())

    def zoom_in(self):
        """If allowed, zooms in by adjusting the pixel hex res."""
        center_hex = self.grid.hexagon_at_center()

        # Only zooms in if allowed.
        if not self.grid.adjust_res(Model.factor):
            return False

        self.grid.update_size()
        self.set_scroll_area()
        self.set_view_to_center(center_hex)

    def zoom_out(self):
        """If allowed, zooms out by adjusting the pixel hex res."""
        center_hex = self.grid.hexagon_at_center()

        # Only zooms out if allowed.
        if not self.grid.adjust_res(-Model.factor):
            return False

        self.grid.update_size()
        self.set_scroll_area()
        self.set_view_to_center(center_hex)

    def set_scroll_area(self):
        """Sets the maximum scrollable area of the view."""
        max_size = self.grid.maximum_size
        self.view.horizontalScrollBar().setMaximum(
            max_size[0] - self.view.rect().width())
        self.view.verticalScrollBar().setMaximum(
            max_size[1] - self.view.rect().height())

    def set_view_to_center(self, hexagon):
        """Sets the center of the view to the given hexagon."""
        center = self.grid.hexgrid.center(hexagon)
        self.view.centerOn(center[0], center[1])
