from constants import *
import animation
from . import thx_map
from . import data

class Level(object):
    """
    This class will be the main class that holds all of the level data.

    It will include a map, a list of enemies, and it should also contain the tiles that it needs
    to display those enemies and that level.
    """
    def __init__(self, n, anim):
        """
        n: An integer between 1 and 16 which will be the level to load.
        """
        if n < 0 or n > (16-1):
            return False

        self.map = thx_map.Map(n)
        (self.monster_positions, header_data) = self.load_monsters(n)
        self.monsters_data = []
        for i in range(0, len(anim)):
            self.monsters_data.append(animation.MonsterClass(anim[i], ord(header_data[i * 2]), 
                    ord(header_data[0x40 + i * 2]), ord(header_data[0x80 + i * 2]), 
                    ord(header_data[0xc0 + i * 2]), ord(header_data[0x100 + i * 2])))

    def tile(self, x, y):
        return self.map.tile(x,y)

    def num_monsters(self):
        return len(self.monsters_data)

    def monsters(self,which):
        """
        This should just return the "which" monster in the level. This will function like the old
        array monsters[], but will be tied to the level.
        """
        return self.monsters_data[which]

    def monster_at(self, x, y):
        try:
            monster =  self.monster_positions[(x, y)]
        except KeyError:
            monster = 0
        return monster

    def load_monsters(self,n):
        content = data.default_data_manager().load_file("BUGDB{0:0>2}.BIN".format(n+1))

        # Ignore the header info for now...
        header_data = content[:BUGDB_HEADER_SIZE]
        i = BUGDB_HEADER_SIZE
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

            i += BUGDB_ENTRY_LENGTH

        bugdict = dict([((x[1], x[2]), x[0]) for x in buglist])

        return (bugdict, header_data)
