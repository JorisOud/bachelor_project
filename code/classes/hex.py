from hexutil import Hex

class Hex_custom(Hex):
    """Inherits from the hex class in hexutil.

    Added two methods in order to be able to add a
    landcover attribute to the class.
    """
    def add_landcover(self, landcover):
        self.landcover = landcover

    def get_landcover(self):
        return self.landcover
