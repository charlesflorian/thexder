from . import data
from constants import *

class Map(object):
    """This will be where the class for storing level data."""

    def __init__(self,n):
        if n < 0 or n > (16-1):
            self.curlvl = 0
        else:
            self.curlvl = n
        self.open_lvl()

    def open_lvl(self):
        """
        This will open the level. This perhaps should be called in the __init__ procedure.
        """
        global LVL_HEIGHT
        dm = data.default_data_manager()
        level_name = "MAP{0:0>2}.BIN".format(self.curlvl + 1)
        raw_level_data = dm.load_file(level_name)
        self.ldata = [[]]
        column_count = 0
        current_column = 0
        for c in raw_level_data:
            # If we've gone over/reached the level height, then we move over to the next column.
            if column_count >= LVL_HEIGHT:
                column_count = 0
                current_column += 1
                self.ldata.append([])

            c = ord(c)
            low = c % 16
            high = c >> 4
            # Two quick modifications: A high bit of 0 means 8 things in a row.
            # High bits of greater than (or equal to) 8 signify a monster.
            # There's also a slight issue here: This loses information when we do th bit about the high
            # bit being greater than 8. But there's no reason this has to be the case; we can store the data
            # in the ldata array, and use the tiles array when we actually display things.
            if high >= 8:
                #
                # This is what remembers whether or not there are monsters as stored in the level file.
                # We should use this if we are actually editing the level files.
                #
                #self.ldata[current_column].append((high << 4) + low)
                #column_count += 1

                # This just ignores them, since we really just load them from BUGDBXX.BIN.
                self.ldata[current_column].append(0)
                column_count += 1
            else:
                if high == 0:
                    high = 8
                for i in range(0, high):
                    self.ldata[current_column].append(low)
                column_count += high

    def write_char(self, f, char, n):
        if n > 8:
            return False
        elif n == 8:
            n = 0
        if (char >> 4) > 0:
            f.write(chr(char))
        else:
            f.write(chr((n << 4) + char))
        return True

    def save(self):
        """
        This, not suprisingly, will save the file.
        It's a little unclear what happens a) to the junk at the end of the file
        b) to the fact that some bits are randomly stored otherwise.

        b) shouldn't matter, but a) might...
        """
        dm = data.default_data_manager()

        with dm.write("MAP{0:0>2}.BIN".format(self.curlvl + 1)) as f:
            for i in range(0, self.width()):
                # Grab the first character from this column.
                last_char = self.tile(i,0)
                char_count = 1

                for j in range(1,self.height(i)):
                    # Grab the next character
                    char = self.tile(i,j)
                    if char != last_char or char_count >= 8:
                        # The character has changed, or we've gone over 8. Write the buffer to the file.
                        self.write_char(f,last_char,char_count)
                        char_count = 1
                    else:
                        # Increment the count.
                        char_count += 1
                    last_char = char

                # Write the last bit to the file.
                self.write_char(f,last_char,char_count)

        return True

    def tile(self,x,y):
        """
        This returns the tile at position x, y. These both start at 0.
        """
        if x < 0 or x >= len(self.ldata):
            return False
        if y < 0 or y >= len(self.ldata[x]):
            return False
        return self.ldata[x][y]

    def change_tile(self,x,y,new_tile):
        """
        This obviously changes the level data by making the tile at position (x,y) to be new_tile.

        The only thing that I need to consider is what to do about tiles with non-zero high bits.
        What should I do there? Leave them be for now?

        (x,y) are the position of the tile to change
        new_tile is (for now) a number between x0 and xF.
        """

        # First, check the bounds.
        if x < 0 or x >= self.width():
            return False
        if y < 0 or y >= self.height(x):
            return False

        self.ldata[x][y] = new_tile
        return True

    def width(self):
        return len(self.ldata)

    def height(self,column=0):
        if column >= self.width():
            return False
        return len(self.ldata[column])

