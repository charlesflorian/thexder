from constants import *

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
            offsets.append(offset)

        # There are 8 tiles.
        self.tiles = []
        for i in range(0,len(offsets)):
            self.tiles.append(TileArray(raw_tiles,offsets[i]))


    def tile(self, n):
        if 0 <= n < len(self.tiles):
            return self.tiles[n]
        raise IOError

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

    def pixel(self, x, y):
        """
        This should treat the tile_array as a whole picture, and return the pixel at (x,y).
        """
        if 0 <= x < self.px_width and 0 <= y < self.px_height:
            tile_x = x / TILE_WIDTH
            tile_y = y / TILE_HEIGHT
            px_x = x % TILE_WIDTH
            px_y = y % TILE_HEIGHT
            return self.tile(tile_x,tile_y).pixel(px_x,px_y)
        return False

    def tile(self, x, y):
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

if __name__ == "__main__":
    print "This should not be loaded by itself."
