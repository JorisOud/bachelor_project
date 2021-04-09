

class Tile:
    """
        This class is used to create tiles for the grid. Parameters for
        initialisation: x(int), y(int), land_cover(string), viewed(bool).
    """

    def __init__(self, x, y, land_cover, viewed = False):
        self.x = x
        self.y = y
        self.land_cover = land_cover
        self.viewed = viewed

    def get_coordinates(self):
        """
        Gives x and y coordinates of tile
        """
        return self.x, self.y

    def get_land_cover(self):
        """
        Gives land cover type
        """
        return self.land_cover

    def get_viewed(self):
        """
        Gives boolean of whether tile has been viewed
        """
        return self.viewed

