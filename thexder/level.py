from constants import *
from . import thx_map

class Level(object):
    """
    This class will be the main class that holds all of the level data.

    It will include a map, a list of enemies, and it should also contain the tiles that it needs
    to display those enemies and that level.
    """
    def __init__(self, n):
        """
        n: An integer between 1 and 16 which will be the level to load.
        """
        if n < 1 or n > 16:
            return False

        self.map = thx_map.Map(n)

    def tile(self, x, y):
        return self.map.tile(x,y)
