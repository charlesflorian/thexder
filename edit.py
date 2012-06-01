from curses import *
from math import *
from random import *
from sys import exit
from os import rename

from log import *
import pygame
from pygame.locals import *

def init_colours():
    # This is the default colour scheme, white text on black background.
    init_pair(1,COLOR_WHITE,COLOR_BLACK)
    # This is the colour scheme for monshters, white text on red background.
    init_pair(2,COLOR_WHITE,COLOR_BLUE)
    # The cursor colours:
    init_pair(3,COLOR_BLACK,COLOR_CYAN)
    # Out of bounds colours:
    init_pair(5,COLOR_YELLOW, COLOR_RED)

    # And now, the colours needed for graphics.
    # These sort of suck, actually, and it'd be nice to fix them.
    # I'm not sure that this can be done in curses though.
    init_pair(10,COLOR_BLACK,COLOR_BLACK)
    init_pair(11,COLOR_RED,COLOR_RED)
    init_pair(12,COLOR_BLACK,COLOR_GREEN)
    init_pair(13,COLOR_GREEN,COLOR_GREEN)
    init_pair(14,COLOR_YELLOW,COLOR_YELLOW)
    init_pair(15,COLOR_BLACK,COLOR_RED)
    init_pair(16,COLOR_YELLOW,COLOR_YELLOW)
    init_pair(17,COLOR_MAGENTA,COLOR_MAGENTA)
    init_pair(18,COLOR_BLACK,COLOR_BLUE)
    init_pair(19,COLOR_MAGENTA,COLOR_MAGENTA)
    init_pair(20,COLOR_BLUE,COLOR_BLUE)
    init_pair(21,COLOR_CYAN,COLOR_CYAN)
    init_pair(22,COLOR_BLACK,COLOR_GREEN)
    init_pair(23,COLOR_MAGENTA,COLOR_MAGENTA)
    init_pair(24,COLOR_BLACK,COLOR_WHITE) #grey?
    init_pair(25,COLOR_WHITE,COLOR_WHITE)

def prompt(window, query):
    alert(window,query)
    echo()
    answer =  window.getstr(SCR_HEIGHT + 1, len(query) + 1)
    noecho()
    window.move(SCR_HEIGHT+1,0)
    window.clrtoeol()
    return answer

def alert(window, phrase):
    window.move(SCR_HEIGHT+1,0)
    window.clrtoeol()
    window.addstr(phrase)

def hline(window, y, length):
    for i in range(0,length):
        window.addch(y,i,"_")

###################################################
#
# This is a list of global constants and variables.
#
###################################################

#These are the screen dimensions (Constants!)
SCR_HEIGHT = 22
SCR_WIDTH = 80

#These are the level dimensions. There is no reason for me to have a fixed width. Also constant.
LVL_HEIGHT = 44

# This is the size of a tile in the file EGABITXX.BIN or TANBITXX.BIN
TILE_SIZE = 0x20

NUM_TILES = 8

TILE_HEIGHT = 0x08
TILE_WIDTH = 0x08

# This is the size of a pointer bit in EGAPTRXX.BIN
PTR_SIZE = 0x08

MAX_ENEMIES = 0x20

MAX_LEVELS = 16

#Which level are we editing?
curlvl = 1

#Are we in editing mode?
edit = False

#Here are some things we might want to do in edit mode:

#This is so we can select a large block and change them all at the same time. Default is False.
selecting = False

# These will be the far corner of the selection box.
select_x = 0
select_y = 0

#Have any changes been made since last save?
changes = False

#These refer to the cursor position
cursor_x = 0
cursor_y = 0

#These refer to the screen position
scr_x = 0
scr_y = 0

#This will be an array consisting of the tiles that will be displayed. This makes it easy to change things.
tiles = [[" ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A","B","C","D","E", "F"],
[" ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A","B","C","D","E", "F"],
[" ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A","B","C","D","E", "F"],
[" ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A","B","C","D","E", "F"]]

COLORS = [pygame.Color(0,0,0), #Black
          pygame.Color(0xfa, 0x80, 0x72), #Salmon?
          pygame.Color(0,255,0), #Green
          pygame.Color(0,100,0), #Dark green
          pygame.Color(0xc7,0x61,0x14), #Brown?
          pygame.Color(100,0,0), #Dark red
          pygame.Color(255,255,100), #Yellow
          pygame.Color(255,0,255), #Magenta
          pygame.Color(0,0,100), #Dark Blue
          pygame.Color(100,0,75), #Dark purple
          pygame.Color(0,0,180), #Blue
          pygame.Color(100,255,255), #Cyan
          pygame.Color(40,40,40), #Dark Grey
          pygame.Color(255,50,255), #Magenta
          pygame.Color(130,130,160), #Blue-Gray
          pygame.Color(255,255,255)] #White

###############################################################################################
#
# Here are the classes that we need.
#
###############################################################################################

class level:
    """This will be where the class for storing level data."""
    
    def __init__(self,n):
        if n < 1 or n > 16:
            self.curlvl = 1
        else:
            self.curlvl = n
        self.open_lvl()
        
    def open_lvl(self):
        """
        This will open the level. This perhaps should be called in the __init__ procedure.
        """
        global LVL_HEIGHT
        f = open("MAP{0:0>2}.BIN".format(self.curlvl),"rb")
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
            # Two quick modifications: A high bit of 0 means 8 things in a row.
            # High bits of greater than (or equal to) 8 signify a monster.
            # There's also a slight issue here: This loses information when we do th bit about the high
            # bit being greater than 8. But there's no reason this has to be the case; we can store the data
            # in the ldata array, and use the tiles array when we actually display things.
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
        f = open("MAP{0:0>2}.BIN".format(self.curlvl),"wb")
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

        # And close the file.
        f.close()

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

    def height(self,column):
        if column >= self.width():
            return False
        return len(self.ldata[column])

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
#   X - x position
#   Y - y position
#
#
# It is worth noting that it appears that the animation, thus, is hard-coded... sort of.
#
##############################################################################################

class enemy:
    """
    This should somehow be the class of a monster. It will consist of at least the animation,
    and also other data.
    """
    def __init__(self):
        pass

class animation:
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
            self.tiles.append(tile_array(raw_tiles,offsets[i]))


    def tile(self, n):
        if 0 <= n < len(self.tiles):
            return self.tiles[n]
        raise IOError


class tile_array:
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
                self.tiles[i].append(tile(raw_tile_string, offsets[i][j]))

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

class tile:
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
        
##################################################################################################
#
# This is the actual stuff to run the `editor'.
#
##################################################################################################

def in_range(a,b,x):
    """
    This function will just test to see if the number x is in the range [a,b], or [b,a], as appropriate.
    """
    if a < b:
        return (a <= x) and (x <= b)
    else:
        return (b <= x) and (x <= a)
        
def display_lvl(win, lvl, x, y):
    """
    This will show on the window win the level lvl, with upper left corner at position x, y in the level.
    """
    global SCR_HEIGHT
    global SCR_WIDTH
    global tiles
    global curlvl
    global edit
    global cursor_x, cursor_y
    for j in range(0,SCR_HEIGHT):
        for i in range(0,SCR_WIDTH):
            tile = lvl.tile(i+x,j+y)
            if tile is False:
                # i.e. if the x, y were out of bounds.
                tile = 0
                colors = [5,5]
            else:
                colors = [1,2]
                if edit:
                    if selecting:
                        if in_range(cursor_x,select_x,i) and in_range(cursor_y, select_y,j):
                            colors = [3,3]
                    elif (i,j) == (cursor_x, cursor_y):
                        colors = [3,3]

            high = tile >> 4
                
            if high > 0:
                win.addch(j,i,tiles[(curlvl-1) / 4][tile % 16],color_pair(colors[1]))
                #win.addch(j,i,tiles[(curlvl-1) / 4][tile % 16],color_pair(high + 10))
            else:
                win.addch(j,i,tiles[(curlvl-1) / 4][tile % 16],color_pair(colors[0]))
    hline(win,SCR_HEIGHT,SCR_WIDTH)
    return False

def swap_files(old_file, new_file, fname):
    """
    This will swap two files.

    Input is:
    old_file, new_file: integers between 1 and 16
    fname: a string such as "MAP", "BUGDB", etd.
    """
    rename(fname.upper() + "{0:0>2}.BIN".format(old_file),"temp")
    rename(fname.upper() + "{0:0>2}.BIN".format(new_file),fname.upper() + "{0:0>2}.BIN".format(old_file))
    rename("temp",fname.upper() + "{0:0>2}.BIN".format(new_file))

##########################################################################################
#
# This displays what the tiles look like, four at a time. As it turns out, the tiles are
# all 16 x 16 arrays, and it seems that for levels 1--4 it uses tiles 0x20--0x2F
# while for levels 5--8 it uses tiles 0x10--0x1F. The mapping is exactly what you expect.
#
# Consequently, this should make it very easy to display the level!
#
##########################################################################################

def show_lvl_tiles(tiles,level):
    """
    This will show a preview of the level.
    """
    SCR_WIDTH = 880
    SCR_HEIGHT = 704
    
    pygame.init()
    pygame.key.set_repeat(120,30)
    screen = pygame.display.set_mode((SCR_WIDTH,SCR_HEIGHT))

    graphics = []
    for k in range(0, 16):
        graphics.append(draw_tile(tiles[k],2))

    graphics.append(pygame.Surface((16,16)))
    pygame.draw.rect(graphics[16],(180,0,0),(0,0,16,16),0)

    x_pos = 0
    y_pos = 0

    going = True
    while going:
        for j in range(0,SCR_WIDTH / 16):
            for i in range(0, SCR_HEIGHT / 16):
                cur_tile = level.tile(j + x_pos, i + y_pos)
                if cur_tile is False:
                    cur_tile = 0

                if cur_tile >> 4:
                    screen.blit(graphics[16],(j*16, i * 16))
                else:
                    screen.blit(graphics[cur_tile % 16], (j * 16, i * 16))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if keys[K_UP]:
                #    y_pos -= 1
                #    if y_pos < 0:
                #        y_pos = 0
                    x_pos -= 10
                elif keys[K_DOWN]:
                #    y_pos += 1
                #    if y_pos >= LVL_HEIGHT - SCR_HEIGHT:
                #        y_pos = LVL_HEIGHT - SCR_HEIGHT - 1
                    x_pos += 10
                elif keys[K_RIGHT]:
                    x_pos += 1
                elif keys[K_LEFT]:
                    x_pos -= 1
                else:
                    pygame.display.quit()
                    going = False

                if x_pos < 0:
                    x_pos = 0
                elif x_pos >= 512:
                    x_pos = 511
    

def show_lvl_tiles_old(tiles):
    """
    This function just lets you scroll through the tiles, four at a time. It will be replaced by something that
    lets you see a preview of the level.

    At the same time, I would prefer to keep this to allow myself to easily view through all of these tiles.
    """
    pygame.init()
    pygame.key.set_repeat(120,60)
    screen = pygame.display.set_mode((320,340))

    cur_tile = 0

    going = True
    while going:
        arial_font = pygame.font.SysFont("Arial",15)

        text = arial_font.render("Tile = %d" % cur_tile, True, (255,255,255),(0,0,0))

        screen.blit(draw_tile(tiles[cur_tile]), (0,0))
        screen.blit(draw_tile(tiles[cur_tile + 1]), (160, 0))
        screen.blit(draw_tile(tiles[cur_tile + 2]), (0, 160))
        screen.blit(draw_tile(tiles[cur_tile + 3]), (160, 160))

        screen.blit(text,(5,322))

        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if keys[K_UP] or keys[K_LEFT]:
                    cur_tile -= 4
                    if cur_tile < 0:
                        cur_tile = 0
                elif keys[K_DOWN] or keys[K_RIGHT]:
                    cur_tile += 4
                    if cur_tile >= len(tiles):
                        cur_tile = len(tiles) - 1
                else:
                    pygame.display.quit()
                    going = False
    
    pygame.display.quit()


def show_tiles(w, raw_tiles, raw_pointers):
    """
    This is intended to be a function for switching into the mode of showing tiles instead of the level.
    It needs to have w, the window, passed, as well as the current level to look at.

    Also, the raw tile data is passed. I'm not sure quite yet how I want to use it.

    The colours are all screwy (This seems to be a difficulty with the curses
    package), but it is a start...
    """
    global MAX_ENEMIES, NUM_TILES
        
    monsters = []
    for i in range(0,MAX_ENEMIES):
        monsters.append(animation(i,raw_tiles,raw_pointers))

    cur_tile = 0
    cur_monster = 0


    pygame.init()
    pygame.key.set_repeat(120,60)
    screen = pygame.display.set_mode((320,320))


    going = True
    while going:
        # This is probably not too efficient (it re-renders the tile each time), but considering how few I need to
        # render each time (i.e. 1), it doesn't matter.
        screen.blit(draw_tile(monsters[cur_monster].tile(cur_tile)),(0,0))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if keys[K_UP]:
                    cur_monster -= 1
                    if cur_monster < 0:
                        cur_monster = 0
                elif keys[K_DOWN]:
                    cur_monster += 1
                    if cur_monster >= MAX_ENEMIES:
                        cur_monster = MAX_ENEMIES - 1
                elif keys[K_RIGHT]:
                    cur_tile += 1
                    if cur_tile >= NUM_TILES:
                        cur_tile = 0
                elif keys[K_LEFT]:
                    cur_tile -= 1
                    if cur_tile < 0:
                        cur_tile = NUM_TILES - 1
                else:
                    pygame.display.quit()
                    going = False


def draw_tile(tile, size = 20):
    """
    This just draws a tile onto a new pygame.Surface object, and returns that object.

    The surface object it returns is automatically the correct size.
    """
    output = pygame.Surface((size * tile.width(), size * tile.height()))
    for i in range(0, tile.height()):
        for j in range(0, tile.width()):
            pygame.draw.rect(output,COLORS[tile.pixel(j,i)],(j*size,i*size,(j+1)*size,(i+1)*size),0)

    return output


def load_raw_tiles():
    """
    This, similar to the function below, will load all of the tiles from the file

    TNCHRS.BIN
    """
    global TILE_SIZE

    f = open("TNCHRS.BIN","rb")
    content = f.read()
    f.close()

    output = []

    for i in range(0, len(content) / TILE_SIZE ):
        output.append(tile(content,i * TILE_SIZE ))

    return output

                    
def load_raw_animation_data():
    """
    This will just load the raw tiles from the TANBITXX.BIN files.
    This is needed due to the fact that some of the EGAPTRXX.BIN files have pointers
    which go past the end of the corresponding TANBIT file; my guess is that it then reads
    from the previous file.
    """
    global MAX_LEVELS
    output = []

    
    # Get the first set of tiles.
    f = open("TANBIT01.BIN","rb")
    output.append(f.read())
    f.close()
    
    for i in range(1, MAX_LEVELS):
        try:
            # open the next file
            f = open("TANBIT{0:0>2}.BIN".format(i+1),"rb")
            tiles = f.read()
            # if it isn't as long as the previous set of tiles, then we need to borrow from that set.
            if len(tiles) < len(output[-1]):
                tiles += output[-1][len(tiles):]
            output.append(tiles)
            f.close()
        except IOError:
            # alternatively, if the file just doesn't exist (e.g. TANBIT03.BIN) then we just use the previous
            # tiles.
            output.append(output[-1])

    pointers = []
    for i in range(0, MAX_LEVELS):
        f = open("EGAPTR{0:0>2}.BIN".format(i+1),"rb")
        pointers.append(f.read())
        f.close()

    return (output, pointers)


#And here is the main function.
def main(w):
    global SCR_HEIGHT, SCR_WIDTH, LVL_HEIGHT
    global curlvl, edit, selecting, select_x, select_y, changes, cursor_x, cursor_y, scr_x, scr_y
    global tiles

    init_colours()

    (raw_tiles, raw_pointers) = load_raw_animation_data()
    
    working_lvl = level(curlvl)
            
    display_lvl(w,working_lvl,0,0)

    while True:
        ch = w.getch()
        if ch == KEY_LEFT:
            if edit:
                cursor_x -= 1
                if cursor_x < 0:
                    cursor_x = 0
            else:
                scr_x -= 8
                if scr_x < 0:
                    scr_x = 0
        elif ch == KEY_UP:
            if edit:
                cursor_y -= 1
                if cursor_y < 0:
                    cursor_y = 0
            else:
                scr_y -= 8
                if scr_y < 0:
                    scr_y = 0
        elif ch == KEY_DOWN:
            if edit:
                cursor_y += 1
                if cursor_y >= SCR_HEIGHT:
                    cursor_y = SCR_HEIGHT - 1
            else:
                scr_y += 8
                if scr_y > LVL_HEIGHT - SCR_HEIGHT:
                    scr_y = LVL_HEIGHT - SCR_HEIGHT
        elif ch == KEY_RIGHT:
            if edit:
                cursor_x += 1
                if cursor_x >= SCR_WIDTH:
                    cursor_x = SCR_WIDTH - 1
            else:
                scr_x += 8
                if scr_x > working_lvl.width() - SCR_WIDTH:
                    scr_x = working_lvl.width() - SCR_WIDTH
        elif ch == ord('s'):
            #Save file
            response = prompt(w, "Are you sure you want to save? (y/n)").lower()
            if response.startswith("y"):
                if working_lvl.save():
                    alert(w,"File saved successfully.")
                else:
                    alert(w,"There was an error saving the file.")
        elif ch == ord('o'):
            # Open a new level.
            new_lvl = prompt(w,"Which level would you like to open?")
            try:
                curlvl = int(new_lvl)
            except ValueError:
                alert(w,"Not a valid level number!")
            else:
                working_lvl = level(curlvl)
                scr_x = 0
                scr_y = 0
        elif ch == ord('m'):
            #Switch modes between editing and moving.
            edit = not edit
            if edit:
                alert(w,"You are now in editing mode.")
                selecting = False
            else:
                alert(w,"You are no longer in editing mode.")
        elif ch == ord('x'):
            #This is to switch between selecting a large box and not.
            if edit:
                if selecting:
                    selecting = False
                else:
                    selecting = True
                    select_x = cursor_x
                    select_y = cursor_y
            else:
                alert(w,"Can't use selection tool while not in edit mode.")
        elif ch == ord('q'):
            # Not surprisingly, this quits.
            if changes:
                response = prompt(w,"Are you sure you want to quit without saving? (y/n)").lower()
                if respons.startswith("y"):
                    break
            else:
                break
        elif ch == ord('w'):
            # This is to swap parts of levels. Though I'm not sure how best to implement this, since
            # the actual data files are in the Dosbox folder...
            while True:
                response = prompt(w, "What is the first level you want to swap?")
                try:
                    old_lvl = int(response)
                    if 1 <= old_lvl <= 16:
                        break
                except ValueError:
                    pass
            while True:
                response = prompt(w, "What is the second level you want to swap?")
                try:
                    new_lvl = int(response)
                    if 1 <= new_lvl <= 16:
                        break
                except ValueError:
                    pass
            while True:
                response = prompt(w, "Binary: 1 = MAP, 2 = BUGDB, 4 = EGABIT, 8 = EGAPTR, 16 = TANBIT:")
                try:
                    swaps = int(response)
                    if 1 <= swaps <= 31:
                        break
                except ValueError:
                    pass
            if swaps & 1:
                swap_files(old_lvl, new_lvl, "MAP")
            if swaps & 2:
                swap_files(old_lvl, new_lvl, "BUGDB")
            if swaps & 4:
                swap_files(old_lvl, new_lvl, "EGABIT")
            if swaps & 8:
                swap_files(old_lvl, new_lvl, "EGAPTR")
            if swaps & 16:
                swap_files(old_lvl, new_lvl, "TANBIT")
        elif ch == ord('t'):
            # This will be a way to look at (and edit?) graphics tiles.
            show_tiles(w,raw_tiles[curlvl-1], raw_pointers[curlvl - 1])
            w.erase()
        elif ch == ord('l'):
            # This will zip along the level proper with actual tiles visible. Whoo!
            lvl_tiles = load_raw_tiles()

            # All of this stuff is just to match the relatively arbitrary decisions made in the game itself.
            if 1 <= curlvl <= 4:
                lower_tile = 0x20
                upper_tile = 0x30
            elif 5 <= curlvl <= 7:
                lower_tile = 0x10
                upper_tile = 0x20
            elif 8 <= curlvl <= 11:
                lower_tile = 0x60
                upper_tile = 0x70
            elif 13 <= curlvl <= 15:
                lower_tile = 0x70
                upper_tile = 0x80
            else:
                lower_tile = 0x00
                upper_tile = 0x10
            show_lvl_tiles(lvl_tiles[lower_tile:upper_tile], working_lvl)
            #show_lvl_tiles_old(lvl_tiles)
        else:
            if edit:
                # This whole bit feels kludgy, but I'm not sure of a better way to do it.
                # All I'm trying to do is figure out the bottom value of the selection versus cursor
                # so that I can use the function range(a,b) with the requisite bottom value.
                # That being done, we run a double for loop over the selected area (which can be a
                # single cell or a range, it doesn't matter).
                if not selecting:
                    select_x = cursor_x
                    select_y = cursor_y
                else:
                    selecting = False

                if select_x < cursor_x:
                    bottom_x = select_x
                    top_x = cursor_x
                else:
                    bottom_x = cursor_x
                    top_x = select_x

                if select_y < cursor_y:
                    bottom_y = select_y
                    top_y = cursor_y
                else:
                    bottom_y = cursor_y
                    top_y = select_y
                
                if ord('0') <= ch and ch <= ord('9'):
                    for i in range(bottom_x,top_x+1):
                        for j in range(bottom_y, top_y + 1):
                            working_lvl.change_tile(scr_x + i,scr_y + j,ch - ord('0'))
                elif ord('a') <= ch and ch <= ord('f'):
                    for i in range(bottom_x,top_x+1):
                        for j in range(bottom_y, top_y + 1):
                            working_lvl.change_tile(scr_x + i,scr_y + j,ch - ord('a') + 10)

        # Until I actually display the cursor... Actually, I think I'll keep this.   
        if edit:
            alert(w,"x = %d, y = %d" % (cursor_x, cursor_y))
        else:
            alert(w,"x = %d, y = %d" % (scr_x, scr_y))
            
        display_lvl(w,working_lvl,scr_x,scr_y)

if __name__ == "__main__":
    wrapper(main)
