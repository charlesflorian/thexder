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


def load_monsters(raw_tiles, raw_pointers):
    global MAX_ENEMIES, NUM_TILES

    monsters = []

    #monsters.append([])
    #for j in range(0, MAX_ENEMIES): # For each monster...
    #    monsters[0].append(animation.Animation(j,raw_tiles[0],raw_pointers[0]))


    for i in range(0, len(raw_tiles)): # For each level...
        monsters.append([])
        for j in range(0, MAX_ENEMIES): # For each monster...
            monsters[i].append(animation.Animation(j,raw_tiles[i],raw_pointers[i]))

    return monsters




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
    monsters = load_monsters(raw_tiles, raw_pointers)

    lvl_tiles = load_raw_tiles()

    levels = load_levels()


    (lower_tile, upper_tile) = tile_bounds()

##########################
#
# This was a separate function before. For now it is included in main(), but this could change.
#
##########################

    screen = display_init(SCR_WIDTH, SCR_HEIGHT)

    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

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
                    #screen.blit(lvl_graphics[17],(j*16, i * 16))
                    #screen.blit(pygame.font.Font(None, 15).render("%x" % monster, False, (255,255,255)),(j*16, i * 16))
                    screen.blit(monsters[curlvl - 1][(monster - 0x80)/4].tile(0), (j*16, i * 16))
                    
                elif cur_tile >> 4:
                    # I actually should maybe do something with this, but I don't know what.
                    pass
                #if cur_tile >> 4:
                    #screen.blit(lvl_graphics[16],(j*16, i * 16))
                    #screen.blit(pygame.font.Font(None, 15).render("%x" % (cur_tile >> 4), False, (255,255,255)),(j*16, i * 16))
                else:
                    screen.blit(lvl_graphics[cur_tile % 16].tile(), (j * 16, i * 16))

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
                    #lvl_graphics = graphics.render_lvl_tiles(lvl_tiles, lower_tile, upper_tile)
                    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

                    x_pos = 0
                elif keys[K_n]:
                    curlvl -= 1
                    if curlvl < 1:
                        curlvl = 1

                    (lower_tile, upper_tile) = tile_bounds(curlvl)
                    #lvl_graphics = graphics.render_lvl_tiles(lvl_tiles, lower_tile, upper_tile)
                    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

                    x_pos = 0

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
