from csv import writer
import re

import hexutil

from .grid import Grid
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets


class Model(QtWidgets.QMainWindow):
    """Represents the GUI with the hexagonal grid and an options menu.

    The GUI contains two major elements: the grid as a QGraphicsView
    and the options menu as a dock widget. The user can zoom in on or
    out of the grid which changes the maximum window boundaries which
    is accounted for by scroll bars with dynamic maxima. The dock widget
    with options include interactive options such as creating, loading,
    saving, or deleting runs.

    Attributes:
    |scene: QGraphicsScene
    |view: QGraphicsView
    |grid: Grid
    |run_list: QListWidget
    |load_from_file_button: QPushButton
    |save_to_file_button: QPushButton
    |selection_label: QLabel
    |run_name_edit: QLineEdit
    |save_run_button: QPushButton
    |delete_run_button: QPushButton
    |create_run_button: QPushButton

    Methods:
    |load_run_from_file(): loads a run or multiple runs from a csv file
    |   or multiple csv files.
    |save_run_to_file(): saves the selected run to a csv file.
    |update_run_list(Run): updates the list with runs by removing,
    |   updating or adding runs.
    |update_run_buttons(Bool): shows or hides the 'save run' and
    |   'delete run' buttons based on the run creation state.
    |update_selection(Hex): updates the GUI options when a hexagon is
    |   (de)selected.
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

        # Creates the grid that visualises all the hexagons by painting.
        self.grid = Grid()

        self.scene.addWidget(self.grid)
        self.setCentralWidget(self.view)

        # Connects scroll movements to update visible window of grid.
        self.view.verticalScrollBar().valueChanged.connect(self.window_change)
        self.view.horizontalScrollBar().valueChanged.connect(self.window_change)

        # Connects a keybind to the zoom in method.
        self.zoom_in_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence('Ctrl++'), self)
        self.zoom_in_shortcut.activated.connect(self.zoom_in)

        # Connects a keybind to the zoom out method.
        self.zoom_out_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence('Ctrl+-'), self)
        self.zoom_out_shortcut.activated.connect(self.zoom_out)

        # Creates the dock widget on the right-hand side of the screen.
        dock_widget = QtWidgets.QDockWidget('Options', self)
        dock_widget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        dock_widget.setFixedWidth(200)

        # Creates the widget with the list with options such as saving a run.
        multi_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        # Creates a list that shows all runs in the current session.
        run_list_box = QtWidgets.QVBoxLayout()
        self.run_list = QtWidgets.QListWidget()
        self.run_list.setMaximumHeight(300)
        self.run_list.itemClicked.connect(self.grid.load_run)
        self.grid.run_list_update.connect(self.update_run_list)
        run_list_box.addWidget(self.run_list)

        # Creates a button that loads a run from a file.
        self.load_from_file_button = QtWidgets.QPushButton(
            "Load Run(s) from File(s)", self)
        self.load_from_file_button.clicked.connect(self.load_run_from_file)
        run_list_box.addWidget(self.load_from_file_button)

        # Creates a button that writes the run hexagons to a csv file.
        self.save_to_file_button = QtWidgets.QPushButton(
            "Save Run to File", self)
        self.save_to_file_button.clicked.connect(self.save_run_to_file)
        self.save_to_file_button.clicked.connect(self.grid.save_current_run)
        self.save_to_file_button.clicked.connect(self.run_list.clearSelection)
        self.save_to_file_button.hide()
        self.run_list.itemClicked.connect(self.save_to_file_button.show)
        run_list_box.addWidget(self.save_to_file_button)

        # Creates the dynamic label that showcases the selected hexagon.
        self.selection_label = QtWidgets.QLabel("Selected hexagon:\n", self)
        self.selection_label.setAlignment(QtCore.Qt.AlignCenter)
        self.grid.selected.connect(self.update_selection)

        # Creates a line edit where user can enter a name for the run.
        self.run_name_edit = QtWidgets.QLineEdit("", self)
        self.run_name_edit.setPlaceholderText("Add a Name")
        self.run_name_edit.hide()

        # Creates the button that saves the current run.
        self.save_run_button = QtWidgets.QPushButton("Save Run", self)
        self.save_run_button.setStyleSheet("background-color : green")
        self.save_run_button.clicked.connect(lambda: self.grid.save_current_run(
            self.run_name_edit.text()))
        self.save_run_button.clicked.connect(self.run_list.clearSelection)
        self.save_run_button.clicked.connect(self.save_to_file_button.hide)
        self.save_run_button.hide()

        # Creates the button that deletes the current run.
        self.delete_run_button = QtWidgets.QPushButton("Delete Run", self)
        self.delete_run_button.setStyleSheet("background-color : red")
        self.delete_run_button.clicked.connect(self.grid.delete_current_run)
        self.delete_run_button.clicked.connect(self.run_list.clearSelection)
        self.delete_run_button.clicked.connect(self.save_to_file_button.hide)
        self.delete_run_button.hide()

        # Creates the button that creates a run.
        self.create_run_button = QtWidgets.QPushButton("Create Run", self)
        self.create_run_button.clicked.connect(self.grid.create_run)
        self.create_run_button.setEnabled(False)
        self.grid.run_creation.connect(self.update_run_buttons)

        # Adds all the buttons and texts to the layout of the dock widget.
        layout.addLayout(run_list_box)
        layout.addWidget(self.selection_label)
        layout.addWidget(self.run_name_edit)
        layout.addWidget(self.save_run_button)
        layout.addWidget(self.delete_run_button)
        layout.addWidget(self.create_run_button)
        multi_widget.setLayout(layout)
        dock_widget.setWidget(multi_widget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)

    def load_run_from_file(self):
        """Loads a run or multiple runs from a file or multiple csv files."""
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self,
            "Load Run(s) from File(s)", "data/runs","CSV Files (*.csv)")

        for file in files:
            with open(file, 'r') as file:
                next(file)
                hexagons = []
                for line in file:
                    # Stops when the footer has been reached.
                    if not line[0].isnumeric():
                        break

                    # Retrieves the hex coords from the file.
                    values = line.split(",")
                    hex_x = int(values[0])
                    hex_y = int(values[1])

                    hex = self.grid.map.tiles[(hex_x, hex_y)]
                    hexagons.append(hex)

                # Retrieve file name without path and extensions.
                file_name = Path(file.name).stem

                self.grid.create_run(file_name, hexagons)

    def save_run_to_file(self):
        """Saves the selected run to a csv file."""
        selected_run = self.run_list.selectedItems()[0].text()
        selected_run_id = int(selected_run.partition(":")[0])
        run_to_be_saved = self.grid.runs[selected_run_id]
        optimal_run = self.grid.optimal_runs[selected_run_id]

        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Run to File", f"data/runs/{run_to_be_saved.name}",
            "CSV files (*.csv)")

        if not file_name:
            self.save_to_file_button.hide()
            return False

        # Removes .csv from the end of file name if necessary.
        file_name = re.sub(r".csv$", "", file_name)

        with open(f"{file_name}.csv", "w", newline='') as file:
            csv_writer = writer(file)

            # Writes the header.
            csv_writer.writerow(["x", "y", "lat", "long", "ribbon",
                                 "x", "y", "lat", "long", "ribbon"])

            visited_trees = []
            optimal_visited_trees = []
            for idx, hex in enumerate(run_to_be_saved.get_hexagons()):
                # Values of the run.
                hex_gps_coords = self.grid.map.get_gps_coords(hex)
                hex_x = hex.x
                hex_y = hex.y
                hex_lat = hex_gps_coords[0]
                hex_long = hex_gps_coords[1]
                ribbon_collected = ""

                # Adds tree number if ribbon collected.
                tree_number = self.grid.map.get_tree_number(hex)
                if tree_number:
                    # Only writes tree number if ribbon has not been collected before.
                    if tree_number not in visited_trees:
                        ribbon_collected = tree_number
                        visited_trees.append(tree_number)

                # Values of the optimal run.
                if idx < len(optimal_run.get_hexagons()):
                    optimal_hex = optimal_run.get_hexagons()[idx]
                    optimal_hex_gps_coords = self.grid.map.get_gps_coords(optimal_hex)
                    optimal_hex_x = optimal_hex.x
                    optimal_hex_y = optimal_hex.y
                    optimal_hex_lat = optimal_hex_gps_coords[0]
                    optimal_hex_long = optimal_hex_gps_coords[1]
                    optimal_ribbon_collected = ""

                    tree_number = self.grid.map.get_tree_number(optimal_hex)
                    if tree_number:
                        # Only writes tree number if ribbon has not been collected before.
                        if tree_number not in optimal_visited_trees:
                            optimal_ribbon_collected = tree_number
                            optimal_visited_trees.append(tree_number)
                else:
                    optimal_hex_x = ""
                    optimal_hex_y = ""
                    optimal_hex_lat = ""
                    optimal_hex_long = ""
                    optimal_ribbon_collected = ""

                csv_writer.writerow([hex_x, hex_y,
                                     hex_lat, hex_long,
                                     ribbon_collected,
                                     optimal_hex_x, optimal_hex_y,
                                     optimal_hex_lat, optimal_hex_long,
                                     optimal_ribbon_collected])

            # Adds a footer with the total length of the run.
            csv_writer.writerow(
                ["length", len(run_to_be_saved.get_hexagons()) * self.grid.map.hex_width,
                "", "", "",
                "optimal length", len(optimal_run.get_hexagons()) * self.grid.map.hex_width])

        self.save_to_file_button.hide()

    @QtCore.pyqtSlot(object)
    def update_run_list(self, run):
        """Updates the list with runs by removing, updating or adding runs."""
        # Checks if the run is already in the list.
        matched_run = self.run_list.findItems(f"{abs(run.run_id)}",
            QtCore.Qt.MatchStartsWith)

        # Removes, updates or adds the run entry.
        if run.run_id < 0 and matched_run:
            idx = self.run_list.indexFromItem(matched_run[0])
            self.run_list.takeItem(idx.row())
        elif matched_run:
            matched_run[0].setText(f"{run.run_id}: {run.name}, {len(run.hexagons)} m")
        elif run.run_id > 0:
            list_name = f"{run.run_id}: {run.name}, {len(run.hexagons)} m"
            self.run_list.addItem(list_name)

    @QtCore.pyqtSlot(bool)
    def update_run_buttons(self, run_creation):
        """Shows or hides the 'save run' and 'delete run' buttons."""
        if run_creation:
            self.create_run_button.setEnabled(False)
            run = self.grid.runs[self.grid.current_run_id]
            self.run_name_edit.setText(f"{run.name}")
            self.run_name_edit.show()
            self.save_run_button.show()
            self.delete_run_button.show()
        else:
            self.create_run_button.setEnabled(True)
            self.run_name_edit.hide()
            self.run_name_edit.clear()
            self.save_run_button.hide()
            self.delete_run_button.hide()

    @QtCore.pyqtSlot(object)
    def update_selection(self, hexagon):
        """Updates the GUI options when a hexagon is (de)selected."""
        if hexagon:
            self.selection_label.setText(
                f"Selected hexagon:\nx={hexagon.x}, y={hexagon.y}")

            # Adds or removes the hexagon if a run is being created.
            if self.grid.run_creation_mode:
                self.grid.modify_current_run(hexagon)
            else:
                self.create_run_button.setEnabled(True)
        else:
            self.selection_label.setText(f"Selected hexagon:\n")
            self.create_run_button.setEnabled(False)

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
