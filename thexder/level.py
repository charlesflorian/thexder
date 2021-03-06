from constants import *
import animation
from . import thx_map
from . import data
from sprites import sprite_collision


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
        #(self.monster_positions, health_gain, enmax_gain, points, motion, health) = self.load_monsters(n)
        (self.monster_dict, health_gain, enmax_gain, points, motion, health) = self.load_monsters(n)
        self.monsters_data = []
        for i in range(0, len(anim)):
            self.monsters_data.append(animation.MonsterClass(anim[i], health_gain[i], 
                    enmax_gain[i], points[i], motion[i], health[i]))

    def block_entry(self):
        self.map.change_tile(18, 11, LEVEL_BLOCK_TILE)
        self.map.change_tile(18, 12, LEVEL_BLOCK_TILE)
        self.map.change_tile(18, 13, LEVEL_BLOCK_TILE)

    def tile(self, x, y):
        return self.map.tile(x,y)

    def tiles(self, frame):
        """
        This should return an array of all the tiles in the given frame.
        """
        output = []
        for i in range(0, frame.width):
            output.append([])
            for j in range(0, frame.height):
                output[i].append(self.tile(frame.x + i, frame.y + j))
                
        return output

    def is_empty(self, frame, check_monsters=False):
        """
        This simply checks as to whether or not the given frame intersects with any tiles in the level.
        """                
        for i in range(0, frame.width):
            for j in range(0, frame.height):
            
                tile = self.map.tile(frame.x + i, frame.y + j) % 16
                
                if tile > 0:
                    return False
                             
        return True

    def num_monsters(self):
        return len(self.monsters_data)

    def monsters(self):
        return self.monster_dict

    def monster_data(self,which):
        """
        This should just return the "which" monster in the level. This will function like the old
        array monsters[], but will be tied to the level.
        """
        return self.monsters_data[which]

    def monster_at(self, x, y):
        """
        For now, this returns a tuple (a, b), where a is the type of the monster (an integer between 0 and 0x20)
        and b is the current health of the monster at the position (x, y).
        """
        for monst in self.monster_dict:
            if self.monster_dict[monst].get_pos() == (x, y):
                return self.monster_dict[monst]
        return -1

    def load_monsters(self,n):
        content = data.default_data_manager().load_file("BUGDB{0:0>2}.BIN".format(n+1))

        # Ignore the header info for now...
        header_data = content[:BUGDB_HEADER_SIZE]

        # Process headers here.
        health_gain = [0] * 0x20
        enmax_gain = [0] * 0x20
        points = [0] * 0x20
        motion = [0] * 0x20
        health = [0] * 0x20
        for i in range(0, 0x20):
            health_gain[i] = ord(header_data[i * 2])
            enmax_gain[i] = ord(header_data[0x40 + i * 2])
            points[i] = ord(header_data[0x80 + i * 2])
            motion[i] = ord(header_data[0xc0 + i * 2])
            health[i] = ord(header_data[0x100 + i * 2])
        # End processing.
        
        i = BUGDB_HEADER_SIZE

        # This should start at 1, since sprite 0 will be the robot.
        m_count = 1
        bug_dict = {}

        while i < len(content):
            bug_offset = ord(content[i])
            bug_x = ord(content[i+2])
            bug_y = ord(content[i+3]) 
            if (bug_y % 2):
                bug_x += 256            
            bug_y /= 2
             
            if (bug_offset != 0) or (bug_x != 0) or (bug_y !=0):
                # The (bug_offset - 0x80) / 4 is just a conversion factor due to how the data is stored in
                # BUGDBXX.BIN.
                
                m_type = (bug_offset - 0x80)/4
                bug_dict[m_count] = animation.Monster(m_count, m_type, motion[m_type],
                        health[m_type], bug_x, bug_y)
                m_count += 1

            i += BUGDB_ENTRY_LENGTH

        return (bug_dict, health_gain, enmax_gain, points, motion, health)
