from constants import *
import graphics

#############################################################################################
#
# In the file BUGDBXX.BIN, the header information is as follows: each type of monster has two bytes
# per 0x40-length chunk. The five chunks are interpreted as follows:
#
# 0x0000 - health gain
# 0x0040 - enmax gain
# 0x0080 - points gain
# 0x00C0 - motion type:
#       00 - no motion.
#       01 - normal slow flying
#       02 - falling
#       03 - slow horizontal motion, no falling.
#       04 - rocket-type loopy motion.
#       05 - falling + slow horizontal motion.
#       06 - hidden (animation is different!), no moving once open.
#       07 - hidden (animation is different!), moves quickly once open.
#       08 - falls, moves randomly-ish.
#       09 - Seems to be about the same as 04?
#       0A - Quick up/down flying (ala bats)
#       0B - Weird jittery flying (also fast)
#       0C - diagonal fall, then no moving.
#       0D - same as 0C
#       0E - same as 0C
#       0F - same as 0C
#
# 0x0100 - health
#
# After this chunk, beginning at 0x0140, there are 12 bytes devoted to each monster.
# I will investigate further what they mean.
#
# Actually, it really seems that there are only 4 bytes. To be fair, not a lot must be encoded:
# Type, x-, y-positions.
#
# A typical one looks like ZWXY where
#   Z - This tells us the type of the enemy. That is, (Z - 0x80)/4 tells us which enemy (starting at the
#       beginning of this file) to use. However, it isn't clear how it is correlated with the graphics;
#       starting at level 4, there is definitely some discrepancy between this use and what comes from
#       EGAPTRXX.BIN.
#   W - 0 always?
#   X - x position:
#       Well, sort of. If Y is even, then this is exactly the x position. if Y is odd, then X + 256 is the x position.
#   Y - y position
#       Close enough. Y / 2 is the y position.
#
#
# It is worth noting that it appears that the animation, thus, is hard-coded... sort of.
#
##############################################################################################

##############################################################################################
#
# It appears that the issue with the graphics is not in any way related to EGAPTRXX.BIN, but
# instead that when we load new tiles over the old ones, that we need to be more choosy somehow
# in how they overwrite old tiles. I may just have to do this by hand, sadly... For example,
# when level 4 is loaded it should overwrite tiles not for the _first_ enemy (which is the
# default), but something a bit later.
#
##############################################################################################

##############################################################################################
#
# It turns out that despite all of the TANXXX.BIN files being in the same format (i.e. a series
# of 8x8 tiles), ROBOT.BIN is different. It is (very likely) a series of images the size of the
# Thexder robot itself. This means that I need to come up with a new tile-loading algorithm...
#
##############################################################################################
class frame(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
class MonsterClass(object):
    """
    This will be the underlying class of a monster. It contains the basic data for each type of monster.

    Each instance of a monster will extend this class in some way, I suppose?
    """
    def __init__(self, animation, health_gain, enmax_gain, points, motion, health):
        self.animation = animation
        self.health_gain = health_gain
        self.enmax_gain = enmax_gain
        self.points = points
        self.motion = motion
        self.health = health

    def tile(self, n):
        return self.animation.tile(n)

    def raw(self, n):
        return self.animation.raw(n)

    def get_health_gain(self):
        return self.health_gain

    def get_enmax_gain(self):
        return self.enmax_gain

    def get_points(self):
        return self.points

    def get_motion(self):
        return self.motion

    def get_health(self):
        return self.health

class Monster(object):

    def __init__(self, ident, monster_class, motion_type, health, x, y):
        """
        ident - refers to their unique id so as not to confuse them with anyone else.
        monster_class - refers to the monster type
        motion_type - refers to the motion type
        health - their original max health.
        x, y - refers to their original position.
        """
        self.monster_class = monster_class
        self.life = health
        self.ident = ident
        self.frame = frame(x, y, 2, 2)
        self.motion = motion_type
        
        self.state = 0
        
    def get_ident(self):
        return self.ident
    
    def get_frame(self):
        return self.frame
        
    def get_motion(self):
        return self.motion
        
    def monster_type(self):
        return self.monster_class

    def frame_no(self, clock):
        if self.get_motion() == 4:# or self.monster_class == 9:
            return self.get_state()
        
        # TODO: This needs to have room for an animation...
        
        elif self.get_motion() == 6:
            return 4 + clock % 4
        elif self.get_motion() == 7:
            return 4 + clock % 4
        return clock

    def health(self):
        return self.life

    def get_pos(self):
        return (self.frame.x, self.frame.y)

    def move_to(self, new_x, new_y):
        self.frame = frame(new_x, new_y, 2, 2)
        
    def get_state(self):
        """
        This is for motion purposes. It permits the monsters to have states that change
        over time. This will be very important, I think.
        """
        return self.state
        
    def set_state(self, state):
        self.state = state
        
    def zap(self):
        self.life -= 1
        return self.health()
        


class Animation(object):
    """
    This will be the class for an animation; it will consist of a collection of tiles.
    """
    def __init__(self, tiles, robot=False):
        """
        tiles: An array of arrays (n x 4) of Tile objects, one for each frame of the animation.
        """

        self.tiles = []
        for i in range(0, len(tiles)):
            self.tiles.append(Tile([[tiles[i][0], tiles[i][1]],[tiles[i][2], tiles[i][3]]]))
                

    def raw(self, n):
        """
        This returns raw tile data (i.e. a rank two array) for the n-th frame.
        """
        if 0 <= n < len(self.tiles):
            return self.tiles[n].tile_raw()
        raise IOError

    def tile(self, n):
        """
        This returns the rendered tile data, as a pygame.Surface object.
        """
        if 0 <= n < len(self.tiles):
            return self.tiles[n].tile()
        raise IOError

    def is_not_blank(self):
        return len(self.tiles) > 0

    @classmethod
    def raw_animation(self,n, tiles, pointers):
        """
        This will take all of the raw tiles and raw pointers, and output an array of tiles that will
        be the animation you care about (the n-th monster).
        """
        global NUM_TILES, MAX_ENEMIES

        if n < 0 or n >= MAX_ENEMIES:
            raise IndexError

        output = []
        for i in range(0, NUM_TILES):
            output.append([])
            for j in range(0, 4):
                ptr = pointers[i * 0x80 + n * 4 + j]
                output[i].append(tiles[ptr[0]][ptr[1]])

        return output


class Tile(object):

    def __init__(self, raw_tile_data, offsets=None, tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT):
        """
        raw_tile_data: a string consisting of the raw tile data e.g. that of TANBITXX.BIN or TNCHRS.BIN.

        offsets: This can be one of two things: either a specific offset into raw_tile_data from which we
                 are to draw a single 8x8 tile, or an array (necessarily rank 2!) from which we will build 
                 an array of tiles.

                 TODO: I should add in some way to check that we actually get a rectangle out of this, or to
                 verify that the offsets[i] are themselves lists...

                 I think that for now I will assume that no empty data will be passed to this, although I
                 feel a little dirty doing that.
        """
        global TILE_SIZE, PX_SIZE, TILE_WIDTH
        
#        if type(offsets) is list:
        if offsets is None:

            height = len(raw_tile_data) * PX_SIZE * TILE_HEIGHT
            width = len(raw_tile_data[0]) * PX_SIZE * TILE_WIDTH
            self.graphic = pygame.Surface((width, height))

            self.raw_data = []
            for i in range(0, len(raw_tile_data)):
                if not type(raw_tile_data[i]) is list:
                    raise TypeError

                for j in range(0, len(raw_tile_data[i])):
                    cur_tile = raw_tile_data[i][j]
                    self.graphic.blit(cur_tile.tile(), (j * PX_SIZE * TILE_WIDTH, i * PX_SIZE * TILE_HEIGHT))

                    # This is just to produce the raw tile data.
                    for k in range(0, TILE_HEIGHT):
                        if j == 0:
                            self.raw_data.append([])
                        self.raw_data[k + i * TILE_HEIGHT].extend(cur_tile.tile_raw()[k])

        else:
            #cur_tile = raw_tile_data[offsets : offsets + TILE_SIZE]
            cur_tile = raw_tile_data[offsets : offsets + tile_width * tile_height / 2]

            # Here we read in the string into an 8x8 array of pixel data.
            self.raw_data = []
            for i in range(0,tile_height):
                self.raw_data.append([])
                for j in range(0,tile_width/2):
                    # Get the high and low bits, separate them into separate pixels.
                    ch = ord(cur_tile[i * tile_width/2 + j])
                    low = ch % 0x10
                    high = ch >> 4
                    self.raw_data[i].extend([high, low])

            self.graphic = graphics.render_tile(self.raw_data, PX_SIZE)

    def tile_raw(self):
        return self.raw_data

    def pixel(self, x, y):
        return self.raw_data[y][x]

    def tile(self):
        return self.graphic

    def width(self):
        return len(self.raw_data[0])

    def height(self):
        return len(self.raw_data)


if __name__ == "__main__":
    print "This should not be loaded by itself."
