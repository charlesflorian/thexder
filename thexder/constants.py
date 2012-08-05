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
          pygame.Color(0xfa, 0x55, 0x55), #Salmon?
          pygame.Color(0,0xaa,0), #Green
          pygame.Color(0x54,0x54,0x54), #Dark green
          pygame.Color(0xaa,0x55,0x00), #Brown?
          pygame.Color(0xaa,0,0), #Dark red
          pygame.Color(0xff,0xff,0x55), #Yellow
          pygame.Color(0xfb,0x54,0xfb), #Magenta
          pygame.Color(0,0,0xaa), #Dark Blue
          pygame.Color(0xaa,0,0xaa), #Dark purple
          pygame.Color(0x55,0x55,0xff), #Blue
          pygame.Color(0x54,0xfb,0xfb), #Cyan
          pygame.Color(0x55,0x55,0x55), #Dark Grey
          pygame.Color(0xff,0x55,0xff), #Magenta
          pygame.Color(0x00,0xaa,0xaa), #Blue-Gray
          pygame.Color(0xfb,0xfb,0xfb)] #White

# Events

TIME_EVENT = pygame.USEREVENT + 1


# Debug stuff.

SPEED = False
