from constants import *

class level:
    """
    This will be the class that consists of all level data: the tiles, the enemies, etc.

    self.ldata will be an rank 2 array which hold the tile data:
    self.ldata[i] is the i-th column, so the (x,y) coordinate is
        self.ldata[y][x]

    where (0,0) is the top left corner.
    """
    def __init__(self, int_lvl):
        """
        int_lvl: An integer between 1 and 16 which will be the level number.
        """
        if int_lvl < 1 or int_lvl > 16:
            self.int_lvl = 1
        else:
            self.int_lvl = int_lvl
            
        self.load_lvl_data()

    def load_lvl_data(self):
        global LVL_HEIGHT
        f = open("MAP{0:0>2}.BIN".format(self.int_lvl),"rb")
        
        self.ldata = [[]]
        column_count = 0
        current_column = 0
        
        while True:
            c = f.read(1)
            if not c:
                break

            # If we've gone over/reached the level height, then we move over to the next column.
            if column_count >= LVL_HEIGHT:
                column_count = 0
                current_column += 1
                self.ldata.append([])

            c = ord(c)
            low = c % 16
            high = c >> 4

            # A high bit of 0 means 8 things in a row.
            #
            # High bits of greater than (or equal to) 8 signify a monster.
            # It's worth keeping this data, although I don't know exactly how it is linked to the
            # enemy data file.

            if high >= 8:
                self.ldata[current_column].append((high << 4) + low)
                column_count += 1
            else:
                if high == 0:
                    high = 8
                for i in range(0, high):
                    self.ldata[current_column].append(low)
                column_count += high

        # Aaaand... close the file.
        f.close()            

    def load_ptr_data(self):
        pass

    def load_enemies(self):
        pass
        
    def load_animations(self):
        pass

    def width(self):
        """
        Returns the width of the level.
        """
        return len(self.ldata)

    def height(self, column = 0):
        """
        Returns the height of the given column, which by default is 0. This should almost invariably
        be the global variable LVL_HEIGHT.
        """
        return len(self.ldata[column])

    def tile(self, x, y):
        """
        This returns the tile at a given coordinate (x, y).

        We take it mod 16 because we don't care about the high bits.
        """
        try:
            return self.ldata[y][x] % 16
        except IndexError:
            # We treat 0 as the default tile. It is a blank tile.
            return 0
