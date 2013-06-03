from math import *
from random import *
from sys import exit
from os import rename
from random import randint

import pygame
from pygame.locals import *

from . import data
from . import config

from . import thx_map
from . import level
from . import animation
from . import graphics
from . import robot

from sprites import *
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
    
    pygame.init()
    #pygame.key.set_repeat(120,30)
    #pygame.key.set_repeat(1, FRAME_LENGTH_MS)
    return pygame.display.set_mode((width,height))


def load_animations(tiles, pointers):

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
    say_what = " " + say_what.upper() + " "

    if center:
        x = (DISPLAY_WIDTH - len(say_what)) / 2
        y = 8

    for i in range(0, len(say_what)):
        display_tile(screen, tiles[ord(say_what[i])].tile(), x + i, y)

    pygame.display.update()
    

# This doesn't seem to work very well? It's skippy...
def display_stats(screen, tiles, thx):
    #tile_size = PX_SIZE * TILE_HEIGHT
    #screen.fill(COLORS[0], pygame.Rect(0,DISPLAY_HEIGHT * tile_size, DISPLAY_WIDTH * tile_size, tile_size))
    
    display_text(screen, "energy", tiles, False, 0, DISPLAY_HEIGHT)
    display_text(screen, "score", tiles, False, 0, DISPLAY_HEIGHT + 2)
    display_text(screen, "level", tiles, False, 16, DISPLAY_HEIGHT + 2)
    display_text(screen, "enmax", tiles, False, 26, DISPLAY_HEIGHT + 2)

def display_tile(screen, tile, x, y):

    tile_size = PX_SIZE * TILE_HEIGHT

#    if (0 <= x < DISPLAY_WIDTH) and (0 <= y < DISPLAY_HEIGHT):
    if (-1 <= x < DISPLAY_WIDTH) and (-1 <= y < SCREEN_HEIGHT):
        screen.blit(tile, (x * tile_size, y * tile_size))
    else:
        raise IndexError # Maybe this is a bad idea...

def display_level(screen, level, tiles, x, y):
    """
    This will show the level in the main frame, starting at the top right corner (x, y).
    """
    
    for j in range(0, DISPLAY_WIDTH):
        for i in range(0, DISPLAY_HEIGHT):
            cur_tile = level.tile(j + x, i + y)
            if cur_tile is False or cur_tile >> 4:
                cur_tile = 0

            display_tile(screen, tiles[cur_tile % 16].tile(), j, i)

def display_sprites(screen, level, frame_number, x, y):

    monsters = level.monsters()

    for monst in monsters:
        sprite = monsters[monst]
        pos = sprite.get_pos()
        if (x - 1 <= pos[0]< x + DISPLAY_WIDTH) and (y - 1 <= pos[1]< y + DISPLAY_HEIGHT):
            # This is just so that each sprite type can have its own way of determining
            # which frame to show.
            cur_frame = monsters[monst].frame_no(frame_number)
            
            display_tile(screen, level.monster_data(sprite.monster_type()).tile(cur_frame),
                    pos[0] - x, pos[1] - y)


# TODO: Include a way to look the other direction, and fix the bounds.

def is_on_screen(screen_x, screen_y, x, y):
    if screen_x < x < screen_x + DISPLAY_WIDTH / 2 and screen_y <= y < screen_y + DISPLAY_HEIGHT:
        return True
    return False

def get_laser_targets(monsters, screen_x, screen_y, east_facing=True):
    out = []
    
    shift = 0
    if east_facing:
        shift = DISPLAY_WIDTH / 2
        
    for monst in monsters:
        pos = monsters[monst].get_pos()
        if is_on_screen(screen_x + shift, screen_y, pos[0], pos[1]):
            out.append(pos)
        if is_on_screen(screen_x + shift, screen_y, pos[0]+1, pos[1]):
            out.append((pos[0] + 1,pos[1]))
        if is_on_screen(screen_x + shift, screen_y, pos[0], pos[1]+1):
            out.append((pos[0],pos[1]+1))
        if is_on_screen(screen_x + shift, screen_y, pos[0]+1, pos[1]+1):
            out.append((pos[0] + 1,pos[1]+1))
    return out

def dir_to_vec(direction):
    if direction == DIR_W:
        return (-2, 0)
    elif direction == DIR_WNW:
        return (-2, -1)
    elif direction == DIR_NW:
        return (-1, -1)
    elif direction == DIR_NNW:
        return (-1, -2)
    elif direction == DIR_N:
        return (0, -2)
    elif direction == DIR_NNE:
        return (1, -2)
    elif direction == DIR_NE:
        return (1, -1)
    elif direction == DIR_ENE:
        return (2, -1)
    elif direction == DIR_E:
        return (2, 0)
    elif direction == DIR_ESE:
        return (2, 1)
    elif direction == DIR_SE:
        return (1, 1)
    elif direction == DIR_SSE:
        return (1, 2)
    elif direction == DIR_S:
        return (0, 2)
    elif direction == DIR_SSW:
        return (-1, 2)
    elif direction == DIR_SW:
        return (-1, 1)
    elif direction == DIR_WSW:
        return (-2, 1)
    raise IndexError

def draw_line(screen, start_x, start_y, direction, color=COLORS[0x0f]):
    """
    This will be the aux method that will draw a line from the (thexder-sized) pixel at
    position given by start_pos and going in the direction given.
    """
#    if direction == (0, 0): # This is something that should never happen, if the enemies can't pass through you.
#        raise ValueError
    
    x_pos = start_x = start_x * PX_SIZE
    y_pos = start_y = start_y * PX_SIZE
    
    try:
        scr_color = screen.get_at((x_pos, y_pos))
    except IndexError:
        return False
    
    while scr_color == COLORS[0]:
        
        screen.fill(color, pygame.Rect(x_pos, y_pos, PX_SIZE, PX_SIZE))
        
        if direction[0] == 0:
            y_pos += PX_SIZE * cmp(direction[1], 0)
        elif abs((y_pos - start_y) * direction[0]) >= abs((x_pos - start_x) * direction[1]):
            x_pos += PX_SIZE * cmp(direction[0], 0)
        else:
            y_pos += PX_SIZE * cmp(direction[1], 0)
            
        try:
            scr_color = screen.get_at((x_pos, y_pos))
        except IndexError:
            pygame.display.update()
            return False
    
    pygame.display.update()
    
    # This should return the sprite id, if it hits a sprite. Or some way of hitting a wall?
    
    return (x_pos / PX_SIZE, y_pos / PX_SIZE)

def draw_laser(screen, start_x, start_y, direction, facing):
    """
    This will draw the laser from the tile located at screen position (start_x, start_y) in the direction
    given, offset from the start_x, start_y position by the value of the tuple facing.
    """
    
    result = draw_line(screen, (start_x + facing[0]) * TILE_WIDTH + TILE_WIDTH / 2,
            (start_y + facing[1]) * TILE_HEIGHT + 3, direction)
    
    if result:        
        return (result[0] / TILE_WIDTH, result[1] / TILE_HEIGHT)
    return False        
    

def target_hit(level, x, y):
    """
    This should tell you what is at the location (x, y) in case you hit it.
    """
    hit_tile = level.tile(x, y)
    if hit_tile:
    
        # TODO: Sort out exactly which tiles we can destroy. In most levels, 0x0d is correct.
        
        return (0, x, y, hit_tile)
        
    monst = sprite_collision(level.monsters(), -1, animation.frame(x,y,1,1))
    if monst:
        # Monsters are killable!
        if not level.monsters()[monst].zap():
        
            ident = level.monsters()[monst].monster_type()
            
            del level.monsters()[monst]
            
            return (1, ident, monst)

        return monst
                    
    return False


##################################################################################################
#
# End display methods.
#
##################################################################################################

def robot_screen_y_pos(robot_y):
    """
    This just let's you know the y-position on the screen of the robot who is at the position
    
    robot_y
    
    in the actual level.
    """
    if robot_y < 11:
        return robot_y
    elif robot_y > LVL_HEIGHT - DISPLAY_HEIGHT / 2:
        return robot_y - (LVL_HEIGHT - DISPLAY_HEIGHT)
    return 11

def main():

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

    screen = display_init(DISPLAY_WIDTH * tile_size, SCREEN_HEIGHT * tile_size)
#    screen = display_init(DISPLAY_WIDTH * tile_size, DISPLAY_HEIGHT * tile_size)

    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

    robot_y = 11 # 11 is the default start.
    robot_x = 19

    x_pos = 0
    y_pos = 0

    game_clock = 0

    pygame.time.set_timer(TIME_EVENT, FRAME_LENGTH_MS)

    display_stats(screen, lvl_tiles, thx)
    
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
        display_sprites(screen, levels[curlvl], game_clock % NUM_TILES, x_pos, y_pos)
        #display_tile(screen, thx.get_frame(), 19, robot_y - y_pos)
        display_tile(screen, thx.frame(), 19, robot_y - y_pos)
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                # We have to check for certain keys, e.g. quit.
                if keys[K_q]:
#                    display_text(screen, "Are you sure you want",lvl_tiles)
#                    display_text(screen, "to quit? (Y/N)", lvl_tiles)
#                    pause()
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

            elif event.type == TIME_EVENT:
                game_clock += 1
            
                move_monsters(levels[curlvl], x_pos, y_pos, robot_x, robot_y, game_clock)
                
                thx.tick()
                
                if thx.wait():
                
                    # While transforming, nothing should happen.
                    
                    pass
                elif thx.is_robot():
                
                    keys = pygame.key.get_pressed()
                    
                    if thx.is_jumping():
                        if keys[K_UP] and thx.jump() and levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True):
                            robot_y -= 1
                        else:
                            if levels[curlvl].is_empty(robot_x, robot_y + 4, 3, 1, True):
                                thx.fall()
                                robot_y += 1
                            else:
                                thx.land()
                    elif thx.is_falling():
                        if levels[curlvl].is_empty(robot_x, robot_y + 4, 3, 1, True):
                            robot_y += 1
                        else:
                            thx.land()
                    elif thx.is_grounded():
                        if keys[K_UP] and levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True):
                            thx.jump()
                            robot_y -= 1
                        elif levels[curlvl].is_empty(robot_x, robot_y + 4, 3, 1, True):
                            thx.fall()
                            robot_y += 1


                    if keys[K_DOWN]:
                        thx.transform()
                    elif keys[K_RIGHT]:
                        if levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 4, True):
                            robot_x += 1
                        thx.push_direction(DIR_E)
                        if thx.is_grounded():
                            thx.step()
                    elif keys[K_LEFT]:
                        if levels[curlvl].is_empty(robot_x - 1, robot_y, 1, 4, True):
                            robot_x -= 1
                        thx.push_direction(DIR_W)
                        if thx.is_grounded():
                            thx.step()
                    
                    
                    # TODO: Something funny here when jumping/falling... 
                         
                    if keys[K_SPACE]:

                        if thx.direction() == DIR_E:
                            targets = get_laser_targets(levels[curlvl].monsters(), x_pos, y_pos, True)

                            if len(targets):
                                target = targets[game_clock % len(targets)]
                                laser_dir = (target[0] - (robot_x + 2), target[1] - robot_y)
                            else:
                                laser_dir = (1,0)
                                
                            result = draw_laser(screen, 20, robot_screen_y_pos(robot_y), laser_dir, (1,0))
                            
                            if result:
                                hit = target_hit(levels[curlvl], result[0] + x_pos, result[1] + y_pos)
                                
                                if hit:
                                    if type(hit) is tuple:
                                        if hit[0] == 0:
                                            if hit[3] in SHOOTABLE_TILES[curlvl]:
                                                levels[curlvl].map.change_tile(hit[1], hit[2], 0x00)
                                        else:
                                            print "Enmax gain: ", levels[curlvl].monster_data(hit[1]).get_enmax_gain()
                                            print "Health gain: ", levels[curlvl].monster_data(hit[1]).get_health_gain()
                                            print "Points gain: ", levels[curlvl].monster_data(hit[1]).get_points()
                        else:
                            targets = get_laser_targets(levels[curlvl].monsters(), x_pos, y_pos, False)
                            
                            if len(targets):
                                target = targets[game_clock % len(targets)]
                                laser_dir = (target[0] - robot_x, target[1] - robot_y)
                            else:
                                laser_dir = (-1,0)
                                
                            result = draw_laser(screen, 20, robot_screen_y_pos(robot_y), laser_dir, (-1,0))
                            
                            if result:
                                hit = target_hit(levels[curlvl], result[0] + x_pos, result[1] + y_pos)

                                if hit:
                                    if type(hit) is tuple:
                                        if hit[0] == 0:
                                            if hit[3] in SHOOTABLE_TILES[curlvl]:
                                                levels[curlvl].map.change_tile(hit[1], hit[2], 0x00)
                                        else:
                                            print "Enmax gain: ", levels[curlvl].monster_data(hit[1]).get_enmax_gain()
                                            print "Health gain: ", levels[curlvl].monster_data(hit[1]).get_health_gain()
                                            print "Points gain: ", levels[curlvl].monster_data(hit[1]).get_points()

                else:
                    thx_blocked = False # Start by assuming that the jet is not blocked in its direction
                                        # of motion. If it turns out to be, then it should try transform.
                    
                    keys = pygame.key.get_pressed()

# TODO: Fix the up/down thing when in a tunnel.

                    if keys[K_UP] and keys[K_LEFT]:
                        if levels[curlvl].is_empty(robot_x - 1, robot_y - 1, 3, 3, True):
                            thx.push_direction(DIR_NW)
                    elif keys[K_UP] and keys[K_RIGHT]:
                        if levels[curlvl].is_empty(robot_x + 1, robot_y - 1, 3, 3, True):
                            thx.push_direction(DIR_NE)
                    elif keys[K_DOWN] and keys[K_LEFT]:
                        if levels[curlvl].is_empty(robot_x - 1, robot_y + 1, 3, 3, True):
                            thx.push_direction(DIR_SW)
                    elif keys[K_DOWN] and keys[K_RIGHT]:                    
                        if levels[curlvl].is_empty(robot_x + 1, robot_y + 1, 3, 3, True):
                            thx.push_direction(DIR_SE)
                    elif keys[K_UP]:
                        thx.push_direction(DIR_N)
                    elif keys[K_DOWN]:
                        thx.push_direction(DIR_S)
                    elif keys[K_LEFT]:
                        if thx.direction() == DIR_E and (levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True) or levels[curlvl].is_empty(robot_x, robot_y + 3, 3, 1, True)):                            
                            thx_blocked = True
                        else:
                            thx.push_direction(DIR_W)
                    elif keys[K_RIGHT]:
                        if thx.direction() == DIR_W and (levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True) or levels[curlvl].is_empty(robot_x, robot_y + 3, 3, 1, True)):
                            thx_blocked = True
                        else:
                            thx.push_direction(DIR_E)

                    direction = thx.direction()
                    if direction == DIR_E:
                        if levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 3, True):
                            robot_x += 1
                        elif levels[curlvl].is_empty(robot_x + 1, robot_y - 1, 3, 3, True):
                            robot_x += 1
                            robot_y -= 1
                            thx.push_direction(DIR_NE)
                        elif levels[curlvl].is_empty(robot_x + 1, robot_y + 1, 3, 3, True):
                            robot_x += 1
                            robot_y += 1
                            thx.push_direction(DIR_SE)
                        else:
                            thx_blocked = True
                    elif direction == DIR_W:
                        if levels[curlvl].is_empty(robot_x - 1, robot_y, 1, 3, True):
                            robot_x -= 1
                        elif levels[curlvl].is_empty(robot_x - 1, robot_y - 1, 3, 3, True):
                            robot_x -= 1
                            robot_y -= 1
                            thx.push_direction(DIR_NW)
                        elif levels[curlvl].is_empty(robot_x - 1, robot_y + 1, 3, 3, True):
                            robot_x -= 1
                            robot_y += 1
                            thx.push_direction(DIR_SW)
                        else:
                            thx_blocked = True
                    elif direction == DIR_N:
                        if levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True):
                            robot_y -= 1
                        elif levels[curlvl].is_empty(robot_x - 1, robot_y - 1, 3, 3, True):
                            robot_x -= 1
                            robot_y -= 1
                            thx.push_direction(DIR_NW)
                        elif levels[curlvl].is_empty(robot_x + 1, robot_y - 1, 3, 3, True):
                            robot_x += 1
                            robot_y -= 1
                            thx.push_direction(DIR_NE)
                        else:
                            thx_blocked = True
                    elif direction == DIR_S:
                        if levels[curlvl].is_empty(robot_x, robot_y + 3, 3, 1, True):
                            robot_y += 1
                        elif levels[curlvl].is_empty(robot_x - 1, robot_y + 1, 3, 3, True):
                            robot_x -= 1
                            robot_y += 1
                            thx.push_direction(DIR_SW)
                        elif levels[curlvl].is_empty(robot_x + 1, robot_y + 1, 3, 3, True):
                            robot_x += 1
                            robot_y += 1
                            thx.push_direction(DIR_SE)
                        else:
                            thx_blocked = True

                    # Diagonals
                    elif direction == DIR_NW:
                        if levels[curlvl].is_empty(robot_x - 1, robot_y - 1, 3,
                                1, True) and levels[curlvl].is_empty(robot_x - 1, robot_y, 1, 2, True):
                            robot_x -= 1
                            robot_y -= 1
                        elif levels[curlvl].is_empty(robot_x - 1, robot_y, 1, 3, True):
                            robot_x -= 1
                            thx.push_direction(DIR_W)
                        elif levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True):
                            robot_y -= 1
                            thx.push_direction(DIR_N)
                        else:
                            thx_blocked = True
                    elif direction == DIR_NE:
                        if levels[curlvl].is_empty(robot_x + 1, robot_y - 1, 3, 
                                1, True) and levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 2, True):
                            robot_x += 1
                            robot_y -= 1
                        elif levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 3, True):
                            robot_x += 1
                            thx.push_direction(DIR_E)
                        elif levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True):
                            robot_y -= 1
                            thx.push_direction(DIR_N)
                        else:
                            thx_blocked = True
                    elif direction == DIR_SE:
                        if levels[curlvl].is_empty(robot_x + 1, robot_y + 3, 3, 
                                1, True) and levels[curlvl].is_empty(robot_x + 3, robot_y + 1, 1, 2, True):
                            robot_x += 1
                            robot_y += 1
                        elif levels[curlvl].is_empty(robot_x + 3, robot_y, 1, 3, True):
                            robot_x += 1
                            thx.push_direction(DIR_E)
                        elif levels[curlvl].is_empty(robot_x, robot_y + 3, 3, 1, True):
                            robot_y += 1
                            thx.push_direction(DIR_S)
                        else:
                            thx_blocked = True
                    elif direction == DIR_SW:
                        if levels[curlvl].is_empty(robot_x - 1, robot_y + 3, 3, 
                                1, True) and levels[curlvl].is_empty(robot_x - 1, robot_y + 1, 1, 2, True):
                            robot_x -= 1
                            robot_y += 1
                        elif levels[curlvl].is_empty(robot_x - 1, robot_y, 1, 3, True):
                            robot_x -= 1
                            thx.push_direction(DIR_W)
                        elif levels[curlvl].is_empty(robot_x, robot_y + 3, 3, 1, True):
                            robot_y += 1
                            thx.push_direction(DIR_S)
                        else:
                            thx_blocked = True
                    
                    if keys[K_SPACE]:
                        direction = dir_to_vec(thx.facing())
                        result = draw_laser(screen, 20, robot_screen_y_pos(robot_y) + 1, direction, direction)

                        if result:
                            hit = target_hit(levels[curlvl], result[0] + x_pos, result[1] + y_pos)

                            if hit:
                                if type(hit) is tuple:
                                    if hit[0] == 0:
                                        if hit[3] in SHOOTABLE_TILES[curlvl]:
                                            levels[curlvl].map.change_tile(hit[1], hit[2], 0x00)
                                    else:
                                        print "Enmax gain: ", levels[curlvl].monster_data(hit[1]).get_enmax_gain()
                                        print "Health gain: ", levels[curlvl].monster_data(hit[1]).get_health_gain()
                                        print "Points gain: ", levels[curlvl].monster_data(hit[1]).get_points()

                    
                    if thx_blocked:
                        # Try transform; if you can't, then turn around.
                        if levels[curlvl].is_empty(robot_x, robot_y + 3, 3, 1, True):
                            thx.transform()
                        elif levels[curlvl].is_empty(robot_x, robot_y - 1, 3, 1, True):
                            robot_y -= 1
                            thx.transform()
                        else:
                            # TODO: This seems a little off in timing?
                            if thx.direction() == DIR_E:
                                thx.push_direction(DIR_W)
                                robot_x -= 1
                            elif thx.direction() == DIR_W:
                                thx.push_direction(DIR_E)
                                robot_x += 1

                if robot_y < 0:
                    robot_y = 0
                if robot_y > LVL_HEIGHT - 4: # This is a little cheeky, since for a plane you 
                                             # _technically_ could be lower than this...
                    robot_y = LVL_HEIGHT - 4
                    
                    
##############################


def cli():
    config.set_app_config_from_cli(config.base_argument_parser())
    return main()

if __name__ == "__main__":
    cli()
