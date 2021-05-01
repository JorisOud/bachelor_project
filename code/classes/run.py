class Run():
    """Represents an elapsed route, a run, by storing hexagons in order.

    Stores the hexagons by adding hexagons to the beginning or the end
    of the run.

    Attributes:
    |run_id: Int
    |name: String
    |hexagons: [Hex]

    Methods:
    |add_hexagon(Hex): only adds a hexagon to the begining or end
    |   of the run.
    |remove_hexagon(Hex): removes the first or last hexagon of the run.
    |get_hexagons(): returns all the hexagons in the run.
    """
    def __init__(self, uid):
        """Requires a unique ID."""
        self.run_id = uid
        self.name = ""
        self.hexagons = []

    def add_hexagon(self, hexagon):
        """Only adds a hexagon to the beginning or end of the run."""
        if len(self.hexagons) > 0:
            # Adds to end if neighbouring last hex.
            last_hex = self.hexagons[-1]
            if hexagon in last_hex.neighbours():
                self.hexagons.append(hexagon)
                return True

            # Adds to beginning if neighbouring first hex.
            first_hex = self.hexagons[0]
            if hexagon in first_hex.neighbours():
                self.hexagons.insert(0, hexagon)
                return True
        else:
            self.hexagons.append(hexagon)
            return True

        return False

    def remove_hexagon(self, hexagon):
        """Removes the first or last hexagon of the run."""
        if len(self.hexagons) > 1:
            if hexagon == self.hexagons[-1]:
                del self.hexagons[-1]
                return True

            if hexagon == self.hexagons[0]:
                del self.hexagons[0]
                return True

        return False

    def get_hexagons(self):
        """Returns all the hexagons of the run."""
        return self.hexagons
