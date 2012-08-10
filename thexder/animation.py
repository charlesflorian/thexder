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

class Monster(object):
    """
    This will be the underlying class of a monster. I don't know what to do with this.
    """
    def __init__(self):
        pass

class Animation(object):
    """
    This will be the class for an animation; it will consist of a collection of tiles.
    As usual, it takes as input a level number.
    n refers to which monster it should load, which will be some number
    between 0 and the largest number of monsters in that level.
    """
    def __init__(self, n, raw_tiles, pointers):
        global NUM_TILES, PTR_SIZE, MAX_ENEMIES

        if n < 0 or n >= MAX_ENEMIES:
            return False

        offsets = []

        for i in range(0, NUM_TILES):
            # This arcane formula just gets the offset numbers from the file.
            offset = [[ord(pointers[n * PTR_SIZE + i * 0x100]) + 0x0100 * ord(pointers[n * PTR_SIZE + i * 0x100 + 1]),
                       ord(pointers[n * PTR_SIZE + i * 0x100 + 2]) + 0x0100 * ord(pointers[n * PTR_SIZE + i * 0x100 + 3])],
                      [ord(pointers[n * PTR_SIZE + i * 0x100 + 4]) + 0x0100 * ord(pointers[n * PTR_SIZE + i * 0x100 + 5]),
                       ord(pointers[n * PTR_SIZE + i * 0x100 + 6]) + 0x0100 * ord(pointers[n * PTR_SIZE + i * 0x100 + 7])]]
            if offset != [[0,0],[0,0]]:
                offsets.append(offset)

        # There are 8 tiles.
        self.tiles = []
        for i in range(0,len(offsets)):
            self.tiles.append(Tile(raw_tiles,offsets[i]))
            

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



class Tile(object):

    def __init__(self, raw_tile_data, offsets):
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
        
        if type(offsets) is list:

            height = len(offsets) * PX_SIZE * TILE_HEIGHT
            width = len(offsets[0]) * PX_SIZE * TILE_WIDTH
            self.graphic = pygame.Surface((width, height))

            self.raw_data = []
            for i in range(0, len(offsets)):
                if not type(offsets[i]) is list:
                    raise TypeError

                for j in range(0, len(offsets[i])):
                    cur_tile = Tile(raw_tile_data,offsets[i][j])
                    self.graphic.blit(cur_tile.tile(), (j * PX_SIZE * TILE_WIDTH, i * PX_SIZE * TILE_HEIGHT))

                    # This is just to produce the raw tile data.
                    for k in range(0, TILE_HEIGHT):
                        if j == 0:
                            self.raw_data.append([])
                        self.raw_data[k + i * TILE_HEIGHT].extend(cur_tile.tile_raw()[k])

        else:
            cur_tile = raw_tile_data[offsets : offsets + TILE_SIZE]

            # Here we read in the string into an 8x8 array of pixel data.
            self.raw_data = []
            for i in range(0,TILE_HEIGHT):
                self.raw_data.append([])
                for j in range(0,TILE_WIDTH/2):
                    # Get the high and low bits, separate them into separate pixels.
                    ch = ord(cur_tile[i * 4 + j])
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
