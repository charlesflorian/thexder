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
curlvl = 4



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

    if (SPEED):
        speed_lvl = 3
        monsters.append([])
        for j in range(0, MAX_ENEMIES): # For each monster...
            monsters[0].append(animation.Animation(j,raw_tiles[speed_lvl - 1],raw_pointers[speed_lvl - 1]))

        # This just copies all the enemy graphics from the first level for all of them.    
        for j in range(1, len(raw_tiles)):
            monsters.append(monsters[-1])

    # As it stands, this is incredibly slow on loading. A few solutions could be:
    #
    # 1. Load them on each level instead of all at once.
    # 2. Figure out why this is so slow. My guess is that it's doing a lot of junk loading due
    #   to all of the empty space that is in each data file.

    else:
        for i in range(0, len(raw_tiles)): # For each level...
            monsters.append([])
            for j in range(0, MAX_ENEMIES): # For each monster...
                new_monster = animation.Animation(j,raw_tiles[i],raw_pointers[i])
                if new_monster.is_not_blank():
                    monsters[i].append(new_monster)

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
#            print "Level %d tiles has length %x\n" % (i + 1, len(tiles))
            if len(tiles) < len(output[-1]):
#                while len(tiles) < len(output[-1]):
#                    tiles += chr(0x60) * (len(output[-1]) - len(tiles))
                tiles = tiles + output[-1][len(tiles):]
            output.append(tiles)
        except ValueError:
            # alternatively, if the file just doesn't exist (e.g. TANBIT03.BIN) then we just use the previous
            # tiles.
#            print "level %d has no graphics.\n" % (i+1)
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


def view_enemies(screen,monsters):
    which_monster = 0
    frame = 0
    going = True
    while going:
        screen.blit(graphics.render_tile(monsters[which_monster].raw(frame),20),(0,0))
        text = pygame.font.Font(None, 20).render("Enemy: %x, Frame: %x" % (which_monster, frame), False, (100,255,100))
        pygame.draw.rect(screen,(0,0,0),(10,330,200,40),0)
        screen.blit(text,(20, 340))

        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if keys[K_RIGHT]:
                    frame += 1
                    if frame >= 8:
                        frame = 0
                elif keys[K_LEFT]:
                    frame -= 1
                    if frame < 0:
                        frame = 7
                elif keys[K_DOWN]:
                    which_monster += 1
                    if which_monster >= len(monsters):
                        which_monster = 0
                elif keys[K_UP]:
                    which_monster -= 1
                    if which_monster < 0:
                        which_monster = len(monsters) - 1
                elif keys[K_q]:
                    going = False


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

    monst_frame = 0

    pygame.time.set_timer(TIME_EVENT, 100)
    
    going = True
    while going:
        for j in range(0,SCR_WIDTH / 16):
            for i in range(0, SCR_HEIGHT / 16):
                cur_tile = levels[curlvl - 1].tile(j + x_pos, i + y_pos)
                if cur_tile is False:
                    cur_tile = 0

                monster = levels[curlvl - 1].monster_at(j + x_pos, i + y_pos)

                # So there are two sources of how the enemies are shown in this game. One is that
                # the high bits of a tile signify that an enemy will be located there. In such a case,
                # I admit that I have no idea what the low bits signify.
                #
                # To see this, one should use the checking for "cur_tile >> 4".
                #
                # Alternatively, in the BUGDBXX.BIN file, there is data showing where monsters are.
                # This is what the "monster > 0" part checks.
                #
                # Specifically, it returns the offset part of the file which sort of seems to say
                # what the monster is, but it isn't 100% accurate (I'm not really sure what the system
                # there is, either.                

                if monster > 0:
                    #screen.blit(lvl_graphics[17],(j*16, i * 16))
                    screen.blit(monsters[curlvl - 1][(monster - 0x80)/4].tile(monst_frame), (j*16, i * 16))
                    #screen.blit(pygame.font.Font(None, 15).render("%x" % monster, False, (100,255,100)),(j*16, i * 16))
                    
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

                elif keys[K_t]:
                    # I still want to be able to look over the enemy tiles, since this seems to be an issue...
                    view_enemies(screen, monsters[curlvl - 1])
                
                elif keys[K_q]:
                    pygame.display.quit()
                    going = False
                else:
                    pass

                if x_pos < 0:
                    x_pos = 0
                elif x_pos >= 512:
                    x_pos = 511
            elif event.type == TIME_EVENT:
                monst_frame += 1
                if monst_frame >= NUM_TILES:
                    monst_frame = 0
            
##############################


def cli():
    config.set_app_config_from_cli(config.base_argument_parser())
    return main()

if __name__ == "__main__":
    cli()
