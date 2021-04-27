import hexutil

from PyQt5 import QtCore, QtGui, QtWidgets
from ..classes.map import Map

class Grid(QtWidgets.QWidget):
    """Represents the visual hexagonal grid.

    Paints the hexagons that are in the boundaries of the window.
    Each hexagon has a defined pixel size (res) that is used to
    calculate which specific hexagons fit from the bottom left corner
    to the top right corner of the window.

    Attributes:
    |window: Rectangle(Int, Int, Int, Int)
    |res: Int
    |hexgrid: Hexgrid
    |map: Map
    |maximum_size: [Int, Int]

    Methods:
    |update_size(): resizes the widget according to the pixel location
    |   of the hexagon in the bottom right corner.
    |hexagon_at_center(): returns the hexagon at the middle of the window.
    |hexagon_of_pos(pos): returns the hex that belongs to the given
    |   screen coordinate.
    |mousePressEvent(event): handles mouse presses to select hexagons.
    |adjust_res(factor): changes the resolution of the hexagons
    |   so that they become larger or smaller.
    |adjust_window(x, y, width, height): changes the boundaries of
    |   the window.
    |paintEvent(event): draws the hexagons that fit in the window with
    |   a colour based on their land cover.
    """
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.res = 5
        self.hexgrid = hexutil.HexGrid(self.res)

        # Initial visible window.
        size = self.size()
        w = size.width()
        h = size.height()
        self.window = hexutil.Rectangle(w, h, w, h)

        self.map = Map("data/map.png")

        # Initialises GUI objects needed for painting.
        self.pen = QtGui.QPen()
        self.pen.setWidth(2)

        self.setMouseTracking(True)

        self.maximum_size = []
        self.update_size()

    def update_size(self):
        """Resizes according to the hex in the bottom right corner."""
        last_hex_dimensions = self.hexgrid.bounding_box(
            hexutil.Hex(2 * self.map.num_hor, self.map.num_ver))
        bottom_right_pixel = (last_hex_dimensions.x + last_hex_dimensions.width,
                              last_hex_dimensions.y + last_hex_dimensions.height)

        self.resize(bottom_right_pixel[0], bottom_right_pixel[1])
        self.maximum_size = [bottom_right_pixel[0], bottom_right_pixel[1]]

    def hexagon_at_center(self):
        """Returns the hexagon at the middle of the window."""
        xc = int(self.window[0] + self.window[2] / 2)
        yc = int(self.window[1] + self.window[3] / 2)

        return self.hexgrid.hex_at_coordinate(xc, yc)

    def hexagon_of_pos(self, pos):
        """Computes the hexagon at the given screen position."""
        return self.hexgrid.hex_at_coordinate(pos.x(), pos.y())

    def adjust_res(self, factor):
        """Adjusts the visual pixel size of the hexagons if possible."""
        old_res = self.res
        if factor > 0:
            self.res = int(self.res * factor)
        else:
            self.res = int(self.res / -factor)

        if self.res < 5 or self.res > 20:
            self.res = old_res
            return False

        self.hexgrid = hexutil.HexGrid(self.res)

        return True

    def adjust_window(self, x, y, width, height):
        """Adjusts the window that is currently visible.

        The window is adjusted based on the bottom left corner of
        the screen and the width and the height of the screen.
        """
        self.window = hexutil.Rectangle(x, y, width, height)

    def paintEvent(self, event):
        """Draws the hexagons that fit in the window.

        Every hexagon is drawn with a colour that corresponds to
        its land cover property.
        """
        bbox = self.window
        self.hexgrid = hexutil.HexGrid(self.res)
        hexgrid = self.hexgrid

        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            # Sets up drawing state.
            painter.setPen(self.pen)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
            painter.translate(0, 0)

            # Draws all the hexagons that fit in the window (bounding box).
            for hexagon in hexgrid.hexes_in_rectangle(bbox):
                polygon = QtGui.QPolygon(
                    [QtCore.QPoint(*corner) for corner in hexgrid.corners(hexagon)])

                tile = self.map.get_tile(hexagon)

                if tile != 5:
                    colour = self.map.land_covers[tile][0]
                    painter.setBrush(QtGui.QBrush(QtGui.QColor(colour[0],
                                                               colour[1],
                                                               colour[2])))
                    painter.drawPolygon(polygon)
        finally:
            painter.end()
