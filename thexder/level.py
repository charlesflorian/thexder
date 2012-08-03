from constants import *
from . import thx_map
from . import data

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
        self.monsters = self.load_monsters(n)

    def tile(self, x, y):
        return self.map.tile(x,y)

    def monster_at(self, x, y):
        try:
            monster =  self.monsters[(x, y)]
        except KeyError:
            monster = 0
        return monster

    def load_monsters(self,n):
        content = data.default_data_manager().load_file("BUGDB{0:0>2}.BIN".format(n))

        # Ignore the header info for now...
        i = 0x140
        buglist = []

        while i < len(content):
            bug_offset = ord(content[i])
            bug_x = ord(content[i+2])
            bug_y = ord(content[i+3]) 
            if (bug_y % 2):
                bug_x += 256            
            bug_y /= 2
             
            if (bug_offset != 0) or (bug_x != 0) or (bug_y !=0):
                buglist.append((bug_offset, bug_x, bug_y))

            i += 0x0c

        bugdict = dict([((x[1], x[2]), x[0]) for x in buglist])

        return bugdict
