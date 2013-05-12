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
from . import robot

from constants import *

# for debugging: import pdb; pdb.set_trace()

import time

# Which level are we looking at? Note that 0 <= curlvl < 16, i.e. it is off by one from
# the actual level number. Trust me, it's better this way.
curlvl = 0

##########################################################################################
#
# Game stuff.
#
##########################################################################################

robot_x = 19
robot_y = 11

##########################################################################################

def display_init(width, height):
    """
    This just sets up the pygame display.
    """
    global FRAME_LENGTH_MS
    
    pygame.init()
    #pygame.key.set_repeat(120,30)
    #pygame.key.set_repeat(1, FRAME_LENGTH_MS)
    return pygame.display.set_mode((width,height))


def load_animations(tiles, pointers):
    global MAX_ENEMIES, NUM_TILES

    animations = []

    for i in range(0, len(tiles)): # For each level...
        animations.append([])
        for j in range(0, MAX_ENEMIES): # For each monster...
            cur_tiles = animation.Animation.raw_animation(j,tiles,pointers[i])
            new_monster = animation.Animation(cur_tiles)
            if new_monster.is_not_blank():
                animations[i].append(new_monster)

    return animations



def load_raw_tiles(filename="TNCHRS.BIN", tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT):
    """
    This will load all the tiles from the named file.
    """

    content = data.default_data_manager().load_file(filename)

    output = []

    tile_size = tile_width * tile_height /2

    for i in range(0, len(content) / tile_size ):
        output.append(animation.Tile(content,i * tile_size, tile_width, tile_height))

    return output

#######################################################################################################
#
# The idea: Simply load every tile, much the same way the level tiles are loaded. Then use the EGAPTRXX
# files to choose which tiles to load.
#
#######################################################################################################

def load_raw_pointers():
    """
    This just loads the raw pointers, and converts them from hex offsets to integer
    ones.
    """
    global MAX_ENEMIES, MAX_LEVELS, PTR_SIZE
    
    dm = data.default_data_manager()
    pointers = []
    
    for i in range(0, MAX_LEVELS):
        pointers.append([])

        ptrs = dm.load_file("EGAPTR{0:0>2}.BIN".format(i+1))
        for k in range(0, len(ptrs) / PTR_SIZE):
            ptr = ptrs[k * PTR_SIZE: (k + 1) * PTR_SIZE]
            ptr = convert_raw_ptrs(ptr)

            pointers[i].extend(ptr)
            
    return process_raw_pointers(pointers)

def convert_raw_ptrs(pointer):
    """
    All that this does is convert them from a hex number which tells you the offset
    of the tile within the TANBITXX file to an integer telling you which tile in the
    list of tiles it should be. There is nothing fancy here.
    """
    global TILE_SIZE
    offset = [(ord(pointer[0]) + 0x0100 * ord(pointer[1]))/TILE_SIZE,
              (ord(pointer[2]) + 0x0100 * ord(pointer[3]))/TILE_SIZE,
              (ord(pointer[4]) + 0x0100 * ord(pointer[5]))/TILE_SIZE,
              (ord(pointer[6]) + 0x0100 * ord(pointer[7]))/TILE_SIZE]
    return offset

def process_raw_pointers(pointers):
    """
    This will be the function which will take all the converted pointers (which are lists of
    integers at this point) and does all of the fancy magic to turn them into something that
    is useful, i.e. which will allow us to draw the monster data out of it.

    It takes as input all the converted pointers, from which it will work its magic.

    What this should do: Shift all the pointers that need to be shifted, and append a level
    number onto it to tell it from which level tileset it needs to take it.

    The output format for a pointer is:

    (level_from_which_to_load_tile, tile_number_within_that_tileset)
    """
    global MAX_LEVELS, TANBIT_SIZE
    global NUM_TILES

    length = 4 * NUM_TILES
    
    output = [[]]
    # Get the ones from the first level...
    for i in range(0, len(pointers[0])):
        output[0].append((0,pointers[0][i]))

    # This is just to keep track of the last time we re-updated a given tile, so that we know from which
    # level we should take it.
    last_seen = [0] * TANBIT_SIZE[0]

    # Now, get the rest.
    for i in range(1, MAX_LEVELS):
        output.append([])
        
        shift = get_shift(i)
        tile_range = (shift * length, shift * length + TANBIT_SIZE[i])

        for j in range(0, len(pointers[i])):
            if tile_range[0] <= pointers[i][j] < tile_range[1]:
                output[i].append((i, pointers[i][j] - shift * length))
                last_seen[pointers[i][j]] = i
            else:
                prev_lvl = last_seen[pointers[i][j]]
                output[i].append((prev_lvl, pointers[i][j] - get_shift(prev_lvl) * length))

    return output


def get_shift(i):
    """
    This just gets the shifting that you need to do to properly view the tiles. 
    """
    shift = 0

    if i == (4 - 1): # The (4 - 1) is just to make clear that this is for level 4, etc.
        shift = 2
    elif i == (5 - 1):
        shift = 1
    elif i == (8 - 1):
        shift = 2
    elif i == (9 - 1):
        shift = 2
    elif i == (12 - 1):
        shift = 1
    elif i == (13 - 1):
        shift = 1

    return shift
    
def load_animation_tiles():
    global MAX_LEVELS
    output = []

    for i in range(0, MAX_LEVELS):
        try:
            tiles = load_raw_tiles("TANBIT{0:0>2}.BIN".format(i+1))
        except ValueError:
            output.append([])
        else:
            output.append(tiles)

    return output


def tile_bounds(level=0):
    """
    This just sets the bounds, as best as I could tell, for the level tiles.
    """
    if (1-1) <= curlvl <= (4-1):
        lower_tile = 0x20
        upper_tile = 0x30
    elif (5-1) <= curlvl <= (7-1):
        lower_tile = 0x10
        upper_tile = 0x20
    elif (8-1) <= curlvl <= (11-1):
        lower_tile = 0x60
        upper_tile = 0x70
    elif (13-1) <= curlvl <= (15-1):
        lower_tile = 0x70
        upper_tile = 0x80
    else:
        lower_tile = 0x00
        upper_tile = 0x10
    return (lower_tile, upper_tile)


def load_levels():
    """
    This function will return an array consisting of all 16 levels. It also loads all of the animation
    and monster data.
    """
    # This loads the animation data.
    raw_tiles = load_animation_tiles()
    raw_pointers = load_raw_pointers()

    # Now we process it.
    animations = load_animations(raw_tiles, raw_pointers)

    levels = []
    for i in range(0, 16):
        levels.append(level.Level(i, animations[i]))

    return levels

################################################################################################## 
#
# Debug stuff.
#
##################################################################################################

def show_tiles(screen, tileset, anim=False):
    global TILE_WIDTH, TILE_HEIGHT
    global DISPLAY_WIDTH, DISPLAY_HEIGHT
    global PX_SIZE
    robot_frame = 0
    going = True
    while going:
        display_tile(screen, tileset[robot_frame].tile(), 0, 0)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[K_RIGHT]:
                    robot_frame += 1
                    if robot_frame >= len(tileset):
                        robot_frame = 0
                elif keys[K_LEFT]:
                    robot_frame -= 1
                    if robot_frame < 0:
                        robot_frame = len(tileset) - 1
                elif keys[K_q]:
                    going = False

def view_enemies(screen,lvl):
    which_monster = 0
    frame = 0

    monsters = []
    for i in range(0, lvl.num_monsters()):
        monsters.append(lvl.monster_data(i))

    pygame.time.set_timer(TIME_EVENT, 100)

    going = True
    while going:
        screen.blit(graphics.render_tile(monsters[which_monster].raw(frame),20),(0,0))
        text = pygame.font.Font(None, 20).render("Enemy: %x, Frame: %x" % (which_monster, frame), False, (100,255,100))
        pygame.draw.rect(screen,(0,0,0),(10,330,220,50),0)
        screen.blit(text,(20, 340))

        text = pygame.font.Font(None, 20).render("HG: %x, EG: %x, P: %x, M: %x, H: %x" % (monsters[which_monster].get_health_gain(), monsters[which_monster].get_enmax_gain(), monsters[which_monster].get_points(), monsters[which_monster].get_motion(), monsters[which_monster].get_health()), False, (100,255,100))
        screen.blit(text,(20, 360))

        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if keys[K_RIGHT]:
                    which_monster += 1
                    if which_monster >= len(monsters):
                        which_monster = 0
                elif keys[K_LEFT]:
                    which_monster -= 1
                    if which_monster < 0:
                        which_monster = len(monsters) - 1
                elif keys[K_q]:
                    going = False
            elif event.type == TIME_EVENT:
                frame += 1
                if frame >= NUM_TILES:
                    frame = 0

##################################################################################################
#
# End debug stuff.
#
##################################################################################################


##################################################################################################
#
# Display methods.
#
##################################################################################################

def pause():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return pygame.key.get_pressed()

def display_text(screen, say_what, tiles, center=True, x=0, y=0):
    """
    This will display text in the thexder font.
    """
    global DISPLAY_HEIGHT, DISPLAY_WIDTH
    say_what = " " + say_what.upper() + " "

    if center:
        x = (DISPLAY_WIDTH - len(say_what)) / 2
        #y = DISPLAY_HEIGHT / 2
        y = 8

    for i in range(0, len(say_what)):
        display_tile(screen, tiles[ord(say_what[i])].tile(), x + i, y)

    pygame.display.update()
    

def display_tile(screen, tile, x, y):
    global PX_SIZE, TILE_HEIGHT, TILE_WIDTH, DISPLAY_HEIGHT, DISPLAY_WIDTH

    tile_size = PX_SIZE * TILE_HEIGHT

#    if (0 <= x < DISPLAY_WIDTH) and (0 <= y < DISPLAY_HEIGHT):
    if (-1 <= x < DISPLAY_WIDTH) and (-1 <= y < DISPLAY_HEIGHT):
        screen.blit(tile, (x * tile_size, y * tile_size))
    else:
        raise IndexError # Maybe this is a bad idea...

def display_level(screen, level, tiles, x, y):
    """
    This will show the level in the main frame, starting at the top right corner (x, y).
    """
    global DISPLAY_WIDTH, DISPLAY_HEIGHT
    
    for j in range(0, DISPLAY_WIDTH):
        for i in range(0, DISPLAY_HEIGHT):
            cur_tile = level.tile(j + x, i + y)
            if cur_tile is False or cur_tile >> 4:
                cur_tile = 0

            display_tile(screen, tiles[cur_tile % 16].tile(), j, i)

def display_sprites(screen, level, frame, x, y):
    global DISPLAY_WIDTH, DISPLAY_HEIGHT

    monsters = level.monsters()

    for monst in monsters:
        sprite = monsters[monst]
        pos = sprite.get_pos()
        if (x - 1 <= pos[0]< x + DISPLAY_WIDTH) and (y - 1 <= pos[1]< y + DISPLAY_HEIGHT):
            display_tile(screen, level.monster_data(sprite.monster_type()).tile(frame), pos[0] - x, pos[1] - y)

##################################################################################################
#
# End display methods.
#
##################################################################################################

##################################################################################################
#
# Begin interaction methods.
#
##################################################################################################

##################################################################################################
#
# End interaction methods.
#
##################################################################################################


def main():
    global DISPLAY_HEIGHT, DISPLAY_WIDTH, LVL_HEIGHT, NO_MONSTERS
    global PX_SIZE, TILE_HEIGHT, TILE_WIDTH
    global curlvl

    #t1 = time.time()

    lvl_tiles = load_raw_tiles()

    # This loads all of the levels and animation tiles. The Level class contains a map, as
    # well as all the of animation/monster data.
    levels = load_levels()

    thx = robot.Robot()


    (lower_tile, upper_tile) = tile_bounds()

    #t2 = time.time()
    #print "%f seconds\n" % (t2 - t1)

    tile_size = PX_SIZE * TILE_HEIGHT

    screen = display_init(DISPLAY_WIDTH * tile_size, DISPLAY_HEIGHT * tile_size)

    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

    robot_y = 11 # 11 is the default start.
    robot_x = 19

    x_pos = 0
    y_pos = 0

    monst_frame = 0

    pygame.time.set_timer(TIME_EVENT, FRAME_LENGTH_MS)
    
    going = True
    while going:

        y_pos = robot_y - 11
        if y_pos < 0:
            y_pos = 0
        elif y_pos > LVL_HEIGHT - DISPLAY_HEIGHT:
            y_pos = LVL_HEIGHT - DISPLAY_HEIGHT

        x_pos = robot_x - 19
        if x_pos < 0:
            x_pos = 0

        display_level(screen, levels[curlvl], lvl_graphics, x_pos, y_pos)
        display_sprites(screen, levels[curlvl], monst_frame, x_pos, y_pos)
        #display_tile(screen, thx.get_frame(), 19, robot_y - y_pos)
        display_tile(screen, thx.frame(), 19, robot_y - y_pos)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                # We have to check for certain keys, e.g. quit.
                if keys[K_q]:
                    pygame.display.quit()
                    going = False
                # These next two switch from one level to the next.
                elif keys[K_m]:
                    curlvl += 1
                    if curlvl >= 16:
                        curlvl = (16-1)

                    (lower_tile, upper_tile) = tile_bounds(curlvl)
                    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

                    robot_x = 19
                    robot_y = 11
                elif keys[K_n]:
                    curlvl -= 1
                    if curlvl < 0:
                        curlvl = 0

                    (lower_tile, upper_tile) = tile_bounds(curlvl)
                    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

                    robot_x = 19
                    robot_y = 11
                elif keys[K_r]:
                    # This should load and display the thexder robot animation. 
                    #show_tiles(screen, lvl_tiles)
                    show_tiles(screen, thx.get_plane_animation())
                    display_text(screen, "What the what", lvl_tiles)
                    pause()
                    display_text(screen, "No seriously what", lvl_tiles)
                    pause()
                    
                #elif keys[K_t]:
                    # I still want to be able to look over the enemy tiles, since this seems to be an issue...
                #    view_enemies(screen, levels[curlvl])
                else:
                    pass

# TODO: I also need to work out how to change between the different robot states better.

# TODO: Make the flying go!
# TODO: Make the left/right turning while jumping work.

# TODO: Fix animation step glitch at peak of jump
# TODO: Put in landing animation

            elif event.type == TIME_EVENT:
                #thx.update()
                thx.tick()
                if thx.is_transforming():
                    # While transforming, nothing should happen.
                    pass
                elif thx.is_robot():
                    keys = pygame.key.get_pressed()
                    
                    if keys[K_RIGHT]:
                        if levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 4):
                            robot_x += 1
#                        if thx.is_facing_left():
#                            thx.turn()
#                        elif thx.is_grounded():
#                            thx.step()
                    elif keys[K_LEFT]:
                        pass
                    elif keys[K_DOWN]:
                        thx.transform()
                    elif keys[K_UP]:
                        pass

                else:
                    thx_blocked = False # Start by assuming that the jet is not blocked in its direction
                                        # of motion. If it turns out to be, then it should try transform.
                    
                    keys = pygame.key.get_pressed()

                    if keys[K_UP] and keys[K_LEFT]:
                        thx.push_direction(DIR_NW)
                    elif keys[K_UP] and keys[K_RIGHT]:
                        thx.push_direction(DIR_NE)
                    elif keys[K_DOWN] and keys[K_LEFT]:
                        thx.push_direction(DIR_SW)
                    elif keys[K_DOWN] and keys[K_RIGHT]:                    
                        thx.push_direction(DIR_SE)
                    elif keys[K_UP]:
                        thx.push_direction(DIR_N)
                    elif keys[K_DOWN]:
                        thx.push_direction(DIR_S)
                    elif keys[K_LEFT]:
                        if thx.direction() == DIR_E:

                            thx_blocked = True
                        else:
                            thx.push_direction(DIR_W)
                    elif keys[K_RIGHT]:
                        if thx.direction() == DIR_W:

                            thx_blocked = True
                        else:
                            thx.push_direction(DIR_E)
                    
                    direction = thx.direction()
                    if direction == DIR_E:
                        if levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 3):
                            robot_x += 1
                        elif levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 2):
                            robot_x += 1
                            robot_y -= 1
                            thx.set_state(THX_FLYING_NE)
                        elif levels[curlvl].is_empty(robot_x + 3, robot_y + 1, 1, 2):
                            robot_x += 1
                            robot_y += 1
                            thx.set_state(THX_FLYING_SE)
                        else:
                            thx_blocked = True
                        
                            
                    if thx_blocked:
                        # Try transform; if you can't, then turn around.
                        pass



# TODO: This isn't... quite right. This would work very well for all non-hidden monsters.
#       However, those that are hidden have their tiles change based on when they were set loose,
#       not a global systems clock.
                monst_frame += 1
                if monst_frame >= NUM_TILES:
                    monst_frame = 0
            
                if robot_y < 0:
                    robot_y = 0
                if robot_y > LVL_HEIGHT - 4: # This is a little cheeky, since for a plane you _technically_ could be lower than this...
                    robot_y = LVL_HEIGHT - 4
##############################


def cli():
    config.set_app_config_from_cli(config.base_argument_parser())
    return main()

if __name__ == "__main__":
    cli()
