import math

import haversine as hs
import hexutil
import numpy as np

from collections import Counter
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
    |tiles: {Hex: Int}
    |num_hor: Int
    |num_ver: Int

    Methods:
    |get_tile(Hex): returns the land cover if exists, else defaults
    |   to 5 (no land cover).
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

        # Calculates the real-life distance between left and right side.
        loc1 = (52.36226580, 4.94751107)
        loc2 = (52.36226580, 4.95285408)
        distance = hs.haversine(loc1, loc2) * 1000

        # The width represents approximately one meter in real-life.
        w = im.size[0] / distance
        size = w / math.sqrt(3)
        h = 2 * size

        num_hor = int(im.size[0] / w) + 1
        num_ver = int(im.size[1] / h * 4 / 3) + 1

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
                self.tiles[hexutil.Hex(col*2, row)] = land_cover
            else:
                self.tiles[hexutil.Hex(col * 2 + 1, row)] = land_cover

    def get_tile(self, hexagon):
        """Returns the land cover of the hexagon."""
        return self.tiles.get(hexagon, 5)


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
