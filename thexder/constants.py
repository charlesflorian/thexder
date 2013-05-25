import pygame
from pygame.locals import *

#These are the level dimensions. There is no reason for me to have a fixed width. Also constant.
LVL_HEIGHT = 44

# This is the size of a tile in the file EGABITXX.BIN or TANBITXX.BIN
TILE_SIZE = 0x20

NUM_TILES = 8

TILE_HEIGHT = 0x08
TILE_WIDTH = 0x08

# pixel size, since we aren't doing a 1--1 pixel.
PX_SIZE = 0x03

# Display parameters
#
# It should be noted that the values for the game display size are 22 x 40
#
DISPLAY_HEIGHT = 22
DISPLAY_WIDTH = 40

#These are the screen dimensions (Constants!)
SCR_HEIGHT = PX_SIZE * TILE_HEIGHT * DISPLAY_HEIGHT
SCR_WIDTH = PX_SIZE * TILE_WIDTH * DISPLAY_WIDTH

# This is the size of a pointer bit in EGAPTRXX.BIN
PTR_SIZE = 0x08

MAX_ENEMIES = 0x20

MAX_LEVELS = 16

# Animation constants

FRAME_LENGTH_MS = 75

#

BUGDB_HEADER_SIZE = 0x140
BUGDB_ENTRY_LENGTH = 0x0c

TANBIT_SIZE = [0x100,0x100,0xe0,0x20,0x80,0x00,0x40,0x40,0xc0,0x00,0x40,0x40,0x80,0x40,0x40,0xf0]

# Thexder constants

JUMP_MAX_HEIGHT = 16 # 16 is the actual max height.

DIR_W   = 0x00
DIR_WNW = 0x01
DIR_NW  = 0x02
DIR_NNW = 0x03
DIR_N   = 0x04
DIR_NNE = 0x05
DIR_NE  = 0x06
DIR_ENE = 0x07
DIR_E   = 0x08
DIR_ESE = 0x09
DIR_SE  = 0x0a
DIR_SSE = 0x0b
DIR_S   = 0x0c
DIR_SSW = 0x0d
DIR_SW  = 0x0e
DIR_WSW = 0x0f

THX_FLAG_ROBOT          = 0x01
THX_FLAG_JET            = 0x02
THX_FLAG_JUMP           = 0x04
THX_FLAG_FALL           = 0x08
THX_FLAG_TRANSFORMING   = 0x10

THX_FLYING_FRAMES = 0x20


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

#SPEED = False
NO_MONSTERS = False
