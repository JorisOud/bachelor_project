import math
import os

import haversine as hs
import hexutil
import numpy as np

from collections import Counter
from .hex import Hex_custom
from PIL import Image


class Map():
    """Represents a hexagonal grid with a land cover for each tile.

    First, hexagons are created by loading an image of a land cover
    map. The real-life distance from one side of the map to the other
    side is used to calculate the ratio of pixel to meter. Then the
    hexagons are created with doubled coordinates where one hexagon
    has a width of approximately one meter in real-life.

    Attributes:
    |land_covers: {Int: [RGB, String]}
    |top_left_coords: (Float, Float)
    |top_right_coords: (Float, Float)
    |bottom_left_coords: (Float, Float)
    |bottom_right_coords: (Float, Float)
    |hex_width: Float
    |hex_size: Float
    |hex_height: Float
    |num_hor: Int
    |num_ver: Int
    |tiles: {Hex: Int}
    |tree_hexagons: {String: Hex}

    Methods:
    |get_tile(Hex): returns the land cover if exists, else defaults
    |   to 5 (no land cover).
    |get_tree_number(Hex): returns the tree number if the hexagon has a
    | ribbon else returns False.
    |is_passable(Hex): returns true or false depending on if the land
    |   cover associated with the hexagon is passable.
    |cost(Hex): returns the cost of passing through a hexagon based on
    |   its land cover.
    |is_transparent(Hex): returns whether the hexagon is transparent or not.
    |get_gps_coords(Hex): returns the gps coords of the center of the
    |   hex.
    |load_ribbons(File): loads all the ribbons based on the tree number
    |   and converting its corresponding gps coordinate to a hex location.
    |rectangle_corners(center, w, h): helper function to calculate the
    |   rectangular dimensions of the pixel area.
    """
    def __init__(self, path):
        """Requires a path to a 24-bit PNG image."""
        self.land_covers = {
            1: [(0, 255, 0), 'grass'],
            2: [(0, 128, 0), 'bushes'],
            3: [(0, 0, 255), 'water'],
            4: [(128, 128, 128), 'path'],
            5: [(255, 255, 255), 'blank']
        }

        im = Image.open(path)
        I = np.asarray(im)

        # Coordinates of the four corners.
        self.top_left_coords = (52.36226580, 4.94751107)
        self.top_right_coords = (52.36226580, 4.95285498)
        self.bottom_left_coords = (52.35821084, 4.94751107)
        self.bottom_right_coords = (52.35821084, 4.95285498)

        # Calculates the real-life distance between left and right side.
        loc1 = self.top_left_coords
        loc2 = self.top_right_coords
        distance = hs.haversine(loc1, loc2) * 1000

        # The width represents approximately one meter in real-life.
        # These hexagon dimentions are in number of pixels.
        w = im.size[0] / distance
        size = w / math.sqrt(3)
        h = 2 * size

        num_hor = int(im.size[0] / w) + 1
        num_ver = int(im.size[1] / h * 4 / 3) + 1

        # save hexagon dimensions in meters
        self.hex_width = distance / num_hor
        self.hex_size = self.hex_width / math.sqrt(3)
        self.hex_height = 2 * self.hex_size

        self.num_hor = num_hor
        self.num_ver = num_ver
        self.tiles = {}

        # Creates hexagons with a land cover property based on the colour
        # of the images.
        for i in range(0, num_hor*num_ver):
            col = i % num_hor
            row = i // num_hor
            even = row % 2

            # Calculates the dimensions of the hexagon in the image.
            raw = rectangle_corners((col*w + even * w/2, row*h * 3/4), w, h)
            r = []
            for points in raw:
                np0 = int(np.clip(points[0], 0, im.size[0]))
                np1 = int(np.clip(points[1], 0, im.size[1]))
                r.append((np0, np1))

            # Calculates the average colour of the pixel area.
            pixel_area = I[r[0][1]:r[3][1],r[0][0]:r[1][0]]
            colour = np.average(I[r[0][1]:r[3][1],r[0][0]:r[1][0]], axis=(0,1))
            colour = tuple(colour.astype(int))

            # Check if the colour corresponds to one of the land covers
            if not any(colour in val for val in self.land_covers.values()):
                # Find the most common colour of the pixel area.
                if len(colour) != 0:
                    most_freq_colour = Counter(
                        tuple(x) for x in [j for i in pixel_area for j in i]).most_common(1)[0][0]
                    colour = most_freq_colour

                # Assign blank if most common colour does not correspond to a land cover.
                if not any(colour in val for val in self.land_covers.values()):
                    colour = (255, 255, 255)

            # Creates the land cover with a (doubled) coordinate.
            land_cover = [k for k, v in self.land_covers.items() if v[0] == colour][0]

            if even == 0:
                new_hex = Hex_custom(col*2, row)
                new_hex.add_landcover(land_cover)
                self.tiles[(col*2, row)] = new_hex
            else:
                new_hex = Hex_custom(col * 2 + 1, row)
                new_hex.add_landcover(land_cover)
                self.tiles[(col * 2 + 1, row)] = new_hex

        # Loads corrections to the land covers to draw smaller paths.
        with os.scandir("data/map_corrections") as files:
            for file in files:
                with open(file) as file:
                    next(file)

                    for line in file:
                        values = line.split(",")
                        hex_x = int(values[0])
                        hex_y = int(values[1])

                        hex = self.tiles[(hex_x, hex_y)]
                        hex.add_landcover(4)

        self.tree_hexagons = {}

    def get_tile(self, hexagon):
        """Returns the land cover of the hexagon."""
        custom_hex = self.tiles.get((hexagon.x, hexagon.y))
        if not custom_hex:
            return 5

        return custom_hex.get_landcover()

    def get_tree_number(self, hexagon):
        """Returns the tree number of the given hexagon if it has a ribbon."""
        if hexagon not in self.tree_hexagons.values():
            return False

        tree_hexes = self.tree_hexagons.items()
        tree_number = [k for k, v in tree_hexes if v == hexagon][0]

        return tree_number

    def is_passable(self, hexagon):
        """Returns if the hexagon is allowed to be passed through."""
        land_cover = self.get_tile(hexagon)
        if land_cover == 3 or land_cover == 5:
            return False

        return True

    def cost(self, hexagon):
        """Calculates the cost for each land cover to pass through."""
        land_cover = self.get_tile(hexagon)
        # Grass
        if land_cover == 1:
            return 1.5
        # Bushes
        if land_cover == 2:
            return 10
        # Path
        if land_cover == 4:
            return 1

    def is_transparent(self, hexagon):
        """Returns whether the hexagon is transparent or not."""
        if self.get_tile(hexagon) == 5:
            return False

        # Tiles bordering the edge are not transparent.
        if (hexagon.x == 0 or hexagon.y == 0
            or hexagon.x == self.num_hor * 2
            or hexagon.y == self.num_ver):
            neighbours = hexagon.neighbours()
            for neighbour in neighbours:
                if self.get_tile(neighbour) == 5:
                    return False

        return True

    def get_gps_coords(self, hex):
        """Returns the real coordinates of the center of a hexagon."""
        # x coordinate
        x_difference = self.top_right_coords[1] - self.top_left_coords[1]
        x_difference_hex = x_difference / self.num_hor
        x = self.top_left_coords[1] + hex.x / 2 * x_difference_hex

        # y coordinate
        y_difference = self.top_left_coords[0] - self.bottom_left_coords[0]
        y_difference_hex = y_difference / self.num_ver
        y = self.top_left_coords[0] - hex.y * y_difference_hex

        return (y, x)

    def load_ribbons(self, file_path):
        """Loads all the ribbons from the specified file into the model on
        the basis of their gps coordinates.
        """
        self.tree_hexagons.clear()
        with open(file_path) as file:
            next(file)

            # put each hexagon with a ribbon in it into a dictionary
            for line in file:
                # get the gps coordinates of a ribbon
                values = line.split(",")
                y_gps, x_gps = float(values[0]), float(values[1])

                # determine y coordinate of the corresponding hexagon in model
                loc1 = self.top_left_coords
                loc2 = (y_gps, self.top_left_coords[1])
                dist_from_top = hs.haversine(loc1, loc2) * 1000
                y_model = int(round(dist_from_top / (self.hex_height * 3/4)))

                # determine x coordinate of the corresponding hexagon in model
                loc2 = (self.top_left_coords[0], x_gps)
                dist_from_left = hs.haversine(loc1, loc2) * 1000

                if y_model % 2 == 0:
                    x_model = int(round(dist_from_left/self.hex_width)) * 2
                else:
                    x_model = int(round((dist_from_left + self.hex_width / 2) /
                                    self.hex_width)) * 2 + 1

                # get hex object form dictionary
                hex = self.tiles.get((x_model, y_model))

                # make sure the ribbon is placed in the right hex, because the x
                # and y of the model are determined with squares instead of hexes
                hex_coords = self.get_gps_coords(hex)
                distance_to_center = hs.haversine((y_gps, x_gps), hex_coords)
                neighbours = hex.neighbours()

                for neighbour in neighbours:
                    neighbour_coords = self.get_gps_coords(neighbour)
                    distance_to_neighbour = hs.haversine((y_gps, x_gps),
                                                    (neighbour.x, y_model))
                    if distance_to_center > distance_to_neighbour:
                        hex = neighbour
                        break

                # put hexagon in dictionary
                self.tree_hexagons[values[2]] = hex


def rectangle_corners(center, w, h):
    """Helper function to calculate the dimensions of the pixel area."""
    x = center[0]
    y = center[1]

    return [
        (x - w/2, y - h/2),
        (x + w/2 , y - h/2),
        (x +w/2, y + h/2),
        (x -w /2, y + h/2)
    ]
