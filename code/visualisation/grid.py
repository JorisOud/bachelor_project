import hexutil

from ..classes.map import Map
from ..classes.run import Run
from PyQt5 import QtCore, QtGui, QtWidgets


class Grid(QtWidgets.QWidget):
    """Represents the visual hexagonal grid.

    Paints the hexagons that are in the boundaries of the window.
    Each hexagon has a defined pixel size (res) that is used to
    calculate which specific hexagons fit from the bottom left corner
    to the top right corner of the window. Every hexagon is painted
    with a different colour based on its land cover. The selected
    hexagon and the hexagons of the current run are painted with a
    special outline colour. The hexagons that include a ribbon are
    given a dot in the center.

    Attributes:
    |res: Int
    |hexgrid: Hexgrid
    |window: Rectangle(Int, Int, Int, Int)
    |Pen: QPen
    |map: Map
    |maximum_size: [Int, Int]
    |selected_hexagon: Hex
    |runs: {Int: Run}
    |run_uid: Int
    |run_creation_mode: Bool
    |current_run_id: Int

    Methods:
    |load_run(run_label): loads the run with the id that is in the given
    |   label of the GUI.
    |create_run(*name, *[Hex]): creates a run with the selected hexagon or
    |   loaded hexagons.
    |modify_current_run(Hex): adds or removes the hex from the current
    |   run if allowed.
    |save_current_run(name): saves the current run to the current session.
    |delete_current_run(): deletes the current run from the current session.
    |mousePressEvent(event): selects or deselects the hexagon that has
    |   been clicked."
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
    # Signals for the mainwindow widget to update GUI elements.
    selected = QtCore.pyqtSignal(object)
    run_creation = QtCore.pyqtSignal(bool)
    run_list_update = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.res = 5
        self.hexgrid = hexutil.HexGrid(self.res)

        # Initial visible window.
        size = self.size()
        w = size.width()
        h = size.height()
        self.window = hexutil.Rectangle(w, h, w, h)

        # Loads the map with its hexagons and land covers.
        self.map = Map("data/map.png")

        # Initialises GUI objects needed for painting.
        self.pen = QtGui.QPen()
        self.pen.setWidth(2)

        # Initialises the window size boundaries of the grid.
        self.maximum_size = []
        self.update_size()

        # Initialises hexagon selection functionality.
        self.setMouseTracking(True)
        self.selected_hexagon = 0

        # Initial parameters related to the creations of runs.
        self.runs = {}
        self.run_uid = 1
        self.run_creation_mode = False
        self.current_run_id = 0

    def load_run(self, run_label):
        """Loads the run provided by the label of the GUI run list."""
        run_id = int(run_label.text().partition(':')[0])
        self.current_run_id = run_id

        # Activates the 'run creation mode' where the user can add
        # more hexagons and save or delete the run.
        self.run_creation_mode = True
        self.run_creation.emit(True)

        self.repaint()

    def create_run(self, name="", hexagons=0):
        """Creates a run with the selected hex or loaded hexagons."""
        new_run = Run(self.run_uid)
        # Creates a loaded run with existing hexagons or brand new one.
        if hexagons:
            for hex in hexagons:
                new_run.add_hexagon(hex)

            # Stores the file name as the name of the run.
            new_run.name = name

            # Signals to the GUI's main window to load the run in the list.
            self.runs[self.run_uid] = new_run
            self.run_list_update.emit(new_run)

            self.run_uid += 1
        else:
            new_run.add_hexagon(self.selected_hexagon)
            self.runs[self.run_uid] = new_run

            self.current_run_id = self.run_uid
            self.run_uid += 1

            # Activates the 'run creation mode' where the user can add
            # more hexagons and save or delete the run.
            self.run_creation.emit(True)
            self.run_creation_mode = True

            self.repaint()

    def modify_current_run(self, hexagon):
        """Adds or removes the hex from the current run if allowed."""
        current_run = self.runs[self.current_run_id]
        if (current_run.add_hexagon(hexagon)
           or current_run.remove_hexagon(hexagon)):
            self.repaint()

    def save_current_run(self, name):
        """Saves the current run to the current session."""
        # Disables the run creation mode and its GUI elements.
        self.run_creation_mode = False
        self.run_creation.emit(False)

        saved_run = self.runs[self.current_run_id]
        if name:
            saved_run.name = name
        # Signals to GUI to add the (edited) run to the list.
        self.run_list_update.emit(saved_run)

        self.repaint()

    def delete_current_run(self):
        """Deletes the current run from the current session."""
        # Disables the run creation mode and its GUI elements.
        self.run_creation_mode = False
        self.run_creation.emit(False)

        # Marks the run id as negative to indicate removal of run in list.
        deleted_run = self.runs[self.current_run_id]
        deleted_run.run_id = -deleted_run.run_id
        self.run_list_update.emit(deleted_run)

        del self.runs[self.current_run_id]
        self.repaint()

    def mousePressEvent(self, event):
        """Selects or deselects the hexagon that has been clicked."""
        clicked_hexagon = self.hexagon_of_pos(event.pos())
        hex = self.map.get_tile(clicked_hexagon)
        # Selects if new hexagon, else deselects the current selection.
        if (self.selected_hexagon != clicked_hexagon and hex != 5):
            self.selected_hexagon = self.map.tiles[clicked_hexagon.x, clicked_hexagon.y]
        else:
            self.selected_hexagon = 0

        self.selected.emit(self.selected_hexagon)
        self.repaint()

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
        its land cover property. Moreover, the selected hexagon is
        given a special outline colour, the hexagons that contain a
        ribbon are marked with a dot, and the hexagons that are in
        the current run are given a special outline colour.
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

            # Draws a dot in every hexagon that contains a ribbon.
            for tree_number in self.map.tree_hexagons:
                hexagon = self.map.tree_hexagons[tree_number]
                location = hexgrid.center(hexagon)
                painter.setPen(QtGui.QPen(QtGui.QColor('red'), 4))
                painter.drawPoint(location[0], location[1])

            # Draws the outline of the selected hexagon.
            if self.selected_hexagon:
                corners = [QtCore.QPoint(*corner) for corner in hexgrid.corners(self.selected_hexagon)]
                painter.setPen(QtGui.QPen(QtGui.QColor('magenta'), 2))
                for i, corner in enumerate(corners):
                    painter.drawLine(corners[-1 + i], corner)

            # Draws the current run in creation.
            if self.run_creation_mode:
                current_run = self.runs[self.current_run_id]
                for coords in current_run.get_hexagons():
                    hexagon = self.map.tiles[coords]
                    corners = [QtCore.QPoint(*corner) for corner in hexgrid.corners(hexagon)]
                    painter.setPen(QtGui.QPen(QtGui.QColor('red'), 2))
                    for i, corner in enumerate(corners):
                        painter.drawLine(corners[-1 + i], corner)

        finally:
            painter.end()
