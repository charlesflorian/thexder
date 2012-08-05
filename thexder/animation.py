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
#   Z - Seems to be an offset into... something?
#       This seems to need to be a multiple of 4, starting at 80.
#       If it goes past the number of monsters (? How does it know?) then it gives junk.
#       If it is less than 80, then it seems to just be tiles.
#       If it is not a multiple of 4 then it gives animations, but they're offset. Also, the monsters
#       in such cases do not die (or not always?)
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
            self.tiles.append(TileArray(raw_tiles,offsets[i]))
            

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


class TileArray(object):
    """
    This will be a class that contains a collection of tiles which fit into some array.
    """
    def __init__(self, raw_tile_string, offsets):
        """
        This should take as input a string which will be the raw tile data e.g. the contents
        of one of the files TANBITXX.BIN, as well as an array (of arrays) of offsets

        One change I might like to implement is to allow for offsets to just be an array as well,
        but for now this is easier.
        """
        global TILE_WIDTH, TILE_HEIGHT

        self.tiles = []
        for i in range(0, len(offsets)):
            self.tiles.append([])
            for j in range(0, len(offsets[i])):
                self.tiles[i].append(Tile(raw_tile_string, offsets[i][j]))

        self.tiles_width = len(offsets[0])
        self.tiles_height = len(offsets)
        self.px_width = self.tiles_width * TILE_WIDTH
        self.px_height = self.tiles_height * TILE_HEIGHT

        self.raw_tile_data = self.make_raw()

        self.graphic = self.render()

    def pixel(self, x, y):
        """
        This should treat the tile_array as a whole picture, and return the pixel at (x,y).
        """
        if 0 <= x < self.px_width and 0 <= y < self.px_height:
            tile_x = x / TILE_WIDTH
            tile_y = y / TILE_HEIGHT
            px_x = x % TILE_WIDTH
            px_y = y % TILE_HEIGHT
            return self.part(tile_x,tile_y).pixel(px_x,px_y)
        return False

    def part(self, x, y):
        """
        This should return the sub-tile which makes the picture up.
        """
        if 0 <= x < self.tiles_width and 0 <= y < self.tiles_height:
            return self.tiles[y][x]
        return False

    def width(self):
        return self.px_width

    def height(self):
        return self.px_height

    def make_raw(self):
        """
        This will make an array consisting of all of the tile data together.
        """
        output = []
        for i in range(0, self.tiles_height):
            for j in range(0, self.part(0,i).height()):
                output.append([])
                for k in range(0, self.tiles_width):
                    output[j + i * TILE_HEIGHT].extend(self.part(k,i).tile_raw()[j])
        return output

    def tile_raw(self):
        return self.raw_tile_data

    def render(self, px_size=PX_SIZE):
        return graphics.render_tile(self.tile_raw(), PX_SIZE)

    def tile(self):
        return self.graphic

class Tile(object):
    """
    This will be the class for tile data, specifically an 8x8 tile.
    """
    def __init__(self, tiles, offset):
        """
        This has as input the level from which one should load the tile, and start, the offset.
        Then it will just read in the next few bytes.
        """
        global TILE_SIZE
        global TILE_HEIGHT

        cur_tile = tiles[offset : offset + TILE_SIZE]

        # Here we read in the string into an 8x8 array of pixel data.
        self.tile_data = []
        for i in range(0,TILE_HEIGHT):
            self.tile_data.append([])
            for j in range(0,TILE_WIDTH/2):
                # Get the high and low bits, separate them into separate pixels.
                ch = ord(cur_tile[i * 4 + j])
                low = ch % 0x10
                high = ch >> 4
                self.tile_data[i].extend([high, low])

        self.offset = offset

        self.graphic = self.render()



    def pixel(self,x,y):
        return self.tile_data[y][x]


    def tile_raw(self):
        return self.tile_data


    def width(self):
        # This should always return the number 8
        return len(self.tile_data[0])


    def height(self):
        # Same here.
        return len(self.tile_data)

    def render(self, px_size=PX_SIZE):
        return graphics.render_tile(self.tile_data, px_size)

    def tile(self):
        return self.graphic

if __name__ == "__main__":
    print "This should not be loaded by itself."
