from curses import *
from math import *
from random import *
from sys import exit
#import pygame
#from pygame.locals import *

def init():
    global scr_height
    window = initscr()
    # Some color stuff...
    start_color()
    # This is the default colour scheme, white text on black background.
    init_pair(1,COLOR_WHITE,COLOR_BLACK)
    # This is the colour scheme for monshters, white text on red background.
    init_pair(2,COLOR_WHITE,COLOR_RED)
    
    noecho()
    cbreak()
    window.keypad(1)
    return window

def fini(window):
    nocbreak()
    window.keypad(0)
    echo()
    endwin()

def prompt(window, query):
    alert(window,query)
    echo()
    answer =  window.getstr(scr_height + 1, len(query) + 1)
    noecho()
    window.move(scr_height+1,0)
    window.clrtoeol()
    return answer

def alert(window, phrase):
    window.move(scr_height+1,0)
    window.clrtoeol()
    window.addstr(phrase)

def hline(window, y, length):
    for i in range(0,length):
        window.addch(y,i,"_")

#These are the screen dimensions
scr_height = 22
scr_width = 80

#These are the level dimensions. I will alter these as we go, they are just a guess right now.
lvl_height = 44
lvl_width = 512

#Which level are we editing?
curlvl = 1

#Are we in editing mode?
edit = False

#Have any changes been made since last save?
changes = False

#These refer to the cursor position
cur_x = 0
cur_y = 0

#These refer to the screen position
scr_x = 0
scr_y = 0

#This will be an array consisting of the tiles.
tiles = [" ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A","B","C","D","E", "X"]

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
        global lvl_height
        f = open("MAP{0:0>2}.BIN".format(self.curlvl),"rb")
        self.ldata = []
        while True:
            c = f.read(1)
            if not c:
                break
            c = ord(c)
            low = c % 16
            high = c >> 4
            # Two quick modifications: A high bit of 0 means 8 things in a row.
            # High bits of greater than 8 signify a monster.
            # There's also a slight issue here: This loses information when we do th bit about the high
            # bit being greater than 8. But there's no reason this has to be the case; we can store the data
            # in the ldata array, and use the tiles array when we actually display things.
            if high > 8:
                self.ldata.append((high << 4) + low)
            else:
                if high == 0:
                    high = 8
                for i in range(0, high):
                    self.ldata.append(low)
        # This last bit is to store the width of the individual level.
        # It should be obvious that having a fixed width of each level 
        # is not ideal.
        self.lwidth = len(self.ldata) / lvl_height

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
        global lvl_height, lvl_width
        f = open("MAP{0:0>2}.BIN".format(self.curlvl),"wb")
        column_count = 1
        char_count = 1
        last_char = self.lvl_raw(0)
        for i in range(1,len(self.ldata)):
            char = self.lvl_raw(i)
            if char != last_char or char_count >= 8 or column_count >= lvl_height:
                # Spit out the buffer!
                self.write_char(f,last_char,char_count)
                char_count = 1
                if column_count >= lvl_height:
                    column_count = 1
                else:
                    column_count = column_count + 1
                last_char = char
            else:
                # Count things up
                char_count = char_count + 1
                column_count = column_count + 1
        # Output what's left
        self.write_char(f,last_char,char_count)
        f.close()
        return True

    def tile(self,x,y):
        """
        This returns the tile at position x, y. These both start at 0.
        """
        global lvl_height
        global lvl_width
        if x < 0 or x > lvl_width or y < 0 or y >= lvl_height or (x * lvl_height + y) >= len(self.ldata):
            return False
        return self.ldata[x * lvl_height + y]

    def lvl_length(self):
        return len(self.ldata)

    def lvl_raw(self, n):
        if n < len(self.ldata) and n >= 0:
            return self.ldata[n]
        return False

    def lvl_raw_data(self):
        return self.ldata

    def width(self):
        return self.lwidth

        
def display_lvl(win, lvl, x, y):
    """
    This will show on the window win the level lvl, with upper left corner at position x, y in the level.
    """
    global scr_height
    global scr_width
    global lvl_height
    global lvl_width
    global tiles
    for j in range(0,scr_height):
        for i in range(0,scr_width):
            tile = lvl.tile(i+x,j+y)
            if tile == False:
                # i.e. if the x, y were out of bounds.
                tile = 0
            high = tile >> 4
            if high > 0:
                win.addch(j,i,tiles[tile % 16],color_pair(2))
            else:
                win.addch(j,i,tiles[tile % 16],color_pair(1))
    hline(win,scr_height,scr_width)
    return False

working_lvl = level(curlvl)
        
w = init()
display_lvl(w,working_lvl,0,0)

while True:
    ch = w.getch()
    if ch == KEY_LEFT:
        scr_x = scr_x - 8
        if scr_x < 0:
            scr_x = 0
    elif ch == KEY_UP:
        scr_y = scr_y - 8
        if scr_y < 0:
            scr_y = 0
    elif ch == KEY_DOWN:
        scr_y = scr_y + 8
        if scr_y > lvl_height - scr_height:
            scr_y = lvl_height - scr_height
    elif ch == KEY_RIGHT:
        scr_x = scr_x + 8
        if scr_x > working_lvl.width() - scr_width:
            scr_x = lvl_width - scr_width
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
    elif ch == ord('q'):
        if changes:
            response = prompt(w,"Are you sure you want to quit without saving? (y/n)").lower()
            if respons.startswith("y"):
                break
        else:
            break
    else:
        pass
    display_lvl(w,working_lvl,scr_x,scr_y)
fini(w)
