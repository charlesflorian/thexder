import pygame
from pygame.locals import *

#These are the screen dimensions (Constants!)
SCR_HEIGHT = 704
SCR_WIDTH = 880

#These are the level dimensions. There is no reason for me to have a fixed width. Also constant.
LVL_HEIGHT = 44

# This is the size of a tile in the file EGABITXX.BIN or TANBITXX.BIN
TILE_SIZE = 0x20

NUM_TILES = 8

TILE_HEIGHT = 0x08
TILE_WIDTH = 0x08

# pixel size, since we aren't doing a 1--1 pixel.
PX_SIZE = 0x02

# This is the size of a pointer bit in EGAPTRXX.BIN
PTR_SIZE = 0x08

MAX_ENEMIES = 0x20

MAX_LEVELS = 16

#

BUGDB_HEADER_SIZE = 0x140
BUGDB_ENTRY_LENGTH = 0x0c


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

# Debug stuff.

SPEED = False
