from math import *
from random import *
from sys import exit
from os import rename

import pygame
from pygame.locals import *

from . import data
from . import config

from . import thx_map
from . import level
from . import animation
from . import graphics

from constants import *

# for debugging: import pdb; pdb.set_trace()


###################################################
#
# This is a list of global constants and variables.
#
###################################################


#Which level are we editing?
curlvl = 1



##########################################################################################
#
# This displays what the tiles look like, four at a time. As it turns out, the tiles are
# all 16 x 16 arrays, and it seems that for levels 1--4 it uses tiles 0x20--0x2F
# while for levels 5--8 it uses tiles 0x10--0x1F. The mapping is exactly what you expect.
#
# Consequently, this should make it very easy to display the level!
#
##########################################################################################

def display_init(width, height):
    """
    This just sets up the pygame display.
    """
    pygame.init()
    pygame.key.set_repeat(120,30)
    return pygame.display.set_mode((width,height))

def render_lvl_tiles(tiles, lower, upper):
    """
    This should take as input a set of tiles and return as output an array of game tiles. These
    will be pygame.Surface objects.
    """
    
    graphics = []
    #for k in range(0, len(tiles)):
    for k in range(lower, upper):
        graphics.append(render_tile(tiles[k],2))

    graphics.append(pygame.Surface((16,16)))

    # Make the last one a blank one.
    pygame.draw.rect(graphics[len(graphics) - 1],(180,0,0),(0,0,16,16),0)

    # This is just so that I can (tentatively) draw monsters.
    graphics.append(pygame.Surface((16,16)))
    pygame.draw.rect(graphics[len(graphics) - 1],(255,75,150),(0,0,16,16),0)

    return graphics




def show_tiles(raw_tiles, raw_pointers):
    """
    This is intended to be a function for switching into the mode of showing tiles instead of the level.
    It needs to have w, the window, passed, as well as the current level to look at.

    Also, the raw tile data is passed. I'm not sure quite yet how I want to use it.
    """
    global MAX_ENEMIES, NUM_TILES

    monsters = []
    for i in range(0,MAX_ENEMIES):
        monsters.append(animation.Animation(i,raw_tiles,raw_pointers))

    cur_tile = 0
    cur_monster = 0


    pygame.init()
    pygame.key.set_repeat(120,60)
    screen = pygame.display.set_mode((320,320))


    going = True
    while going:
        # This is probably not too efficient (it re-renders the tile each time), but considering how few I need to
        # render each time (i.e. 1), it doesn't matter.
        screen.blit(render_tile(monsters[cur_monster].tile(cur_tile)),(0,0))
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
                    #pygame.display.quit()
                    going = False


def render_tile(tile, px_size = 20):
    """
    This just draws a tile onto a new pygame.Surface object, and returns that object.

    The surface object it returns is automatically the correct size.
    """
    output = pygame.Surface((px_size * tile.width(), px_size * tile.height()))
    for i in range(0, tile.height()):
        for j in range(0, tile.width()):
            pygame.draw.rect(output,COLORS[tile.pixel(j,i)],(j*px_size,i*px_size,(j+1)*px_size,(i+1)*px_size),0)

    return output


def load_raw_tiles():
    """
    This, similar to the function below, will load all of the tiles from the file

    TNCHRS.BIN
    """
    global TILE_SIZE

    content = data.default_data_manager().load_file("TNCHRS.BIN")

    output = []

    for i in range(0, len(content) / TILE_SIZE ):
        output.append(animation.Tile(content,i * TILE_SIZE ))

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

    dm = data.default_data_manager()

    # Get the first set of tiles.
    output.append(dm.load_file("TANBIT01.BIN"))

    for i in range(1, MAX_LEVELS):
        try:
            # open the next file
            tiles = dm.load_file("TANBIT{0:0>2}.BIN".format(i+1))
            # if it isn't as long as the previous set of tiles, then we need to borrow from that set.
            if len(tiles) < len(output[-1]):
                tiles += output[-1][len(tiles):]
            output.append(tiles)
        except ValueError:
            # alternatively, if the file just doesn't exist (e.g. TANBIT03.BIN) then we just use the previous
            # tiles.
            output.append(output[-1])

    pointers = []
    for i in range(0, MAX_LEVELS):
        pointers.append(dm.load_file("EGAPTR{0:0>2}.BIN".format(i+1)))

    return (output, pointers)

def tile_bounds(level=1):
    """
    This just sets the bounds, as best as I could tell, for the level tiles.
    """
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
    return (lower_tile, upper_tile)


def load_levels():
    """
    This function will return an array consisting of all 16 levels.
    """
    levels = []
    for i in range(0, 16):
        levels.append(level.Level(i+1))

    return levels

#And here is the main function.
def main():
    global SCR_HEIGHT, SCR_WIDTH, LVL_HEIGHT
    global curlvl

    # Load all the tile data.
    (raw_tiles, raw_pointers) = load_raw_animation_data()
    lvl_tiles = load_raw_tiles()

    levels = load_levels()

    (lower_tile, upper_tile) = tile_bounds()

##########################
#
# This was a separate function before. For now it is included in main(), but this could change.
#
##########################

    screen = display_init(SCR_WIDTH, SCR_HEIGHT)

    lvl_graphics = graphics.render_lvl_tiles(lvl_tiles, lower_tile, upper_tile)

    x_pos = 0
    y_pos = 0

    going = True
    while going:
        for j in range(0,SCR_WIDTH / 16):
            for i in range(0, SCR_HEIGHT / 16):
                cur_tile = levels[curlvl - 1].tile(j + x_pos, i + y_pos)
                if cur_tile is False:
                    cur_tile = 0

                monster = levels[curlvl - 1].monster_at(j + x_pos, i + y_pos)

                if monster > 0:
                    screen.blit(lvl_graphics[17],(j*16, i * 16))
                    screen.blit(pygame.font.Font(None, 15).render("%x" % monster, False, (255,255,255)),(j*16, i * 16))
                elif cur_tile >> 4:
                #if cur_tile >> 4:
                    screen.blit(lvl_graphics[16],(j*16, i * 16))
                    #screen.blit(pygame.font.Font(None, 15).render("%x" % (cur_tile >> 4), False, (255,255,255)),(j*16, i * 16))
                else:
                    screen.blit(lvl_graphics[cur_tile % 16], (j * 16, i * 16))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                # These are the basic motion; for the time being, up/down skip you through the level
                # quickly with left/right being one tile at a time.
                if keys[K_UP]:
                    x_pos -= 10
                elif keys[K_DOWN]:
                    x_pos += 10
                elif keys[K_RIGHT]:
                    x_pos += 1
                elif keys[K_LEFT]:
                    x_pos -= 1

                # These next two switch from one level to the next.
                elif keys[K_m]:
                    curlvl += 1
                    if curlvl > 16:
                        curlvl = 16

                    (lower_tile, upper_tile) = tile_bounds(curlvl)
                    lvl_graphics = graphics.render_lvl_tiles(lvl_tiles, lower_tile, upper_tile)

                    x_pos = 0
                elif keys[K_n]:
                    curlvl -= 1
                    if curlvl < 1:
                        curlvl = 1

                    (lower_tile, upper_tile) = tile_bounds(curlvl)
                    lvl_graphics = graphics.render_lvl_tiles(lvl_tiles, lower_tile, upper_tile)

                    x_pos = 0

                # This is to look at the monster tiles.
                elif keys[K_t]:
                    show_tiles(raw_tiles[curlvl-1], raw_pointers[curlvl - 1])
                else:
                    pygame.display.quit()
                    going = False

                if x_pos < 0:
                    x_pos = 0
                elif x_pos >= 512:
                    x_pos = 511

##############################


def cli():
    config.set_app_config_from_cli(config.base_argument_parser())
    return main()

if __name__ == "__main__":
    cli()
