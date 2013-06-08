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
    #say_what = say_what.upper()

    if center:
        x = (DISPLAY_WIDTH - len(say_what)) / 2
        y = 8

    for i in range(0, len(say_what)):
        display_tile(screen, tiles[ord(say_what[i])].tile(), x + i, y)

    #pygame.display.update()
    

def display_stats(screen, tiles, thx):
    """
    This just displays the status info at the bottom of the screen; the only bit it's missing is that
    at the moment it does not display which level we are on.
    """
    tile_size = PX_SIZE * TILE_HEIGHT
    screen.fill(COLORS[0], pygame.Rect(0,DISPLAY_HEIGHT * tile_size, DISPLAY_WIDTH * tile_size, tile_size * 3))
    
    display_text(screen, "ENERGY", tiles, False, 1, DISPLAY_HEIGHT)    
    display_text(screen, "SCORE", tiles, False, 1, DISPLAY_HEIGHT + 2)
    display_text(screen, "LEVEL", tiles, False, 18, DISPLAY_HEIGHT + 2)
    display_text(screen, "ENMAX", tiles, False, 28, DISPLAY_HEIGHT + 2)

    # The backslash we include is because this is the character in the tileset for the percent sign.
    display_text(screen, "{0:09d}".format(thx.score), tiles, False, 7, DISPLAY_HEIGHT + 2)
    display_text(screen, "{0:03d}".format(thx.get_health()) + "\\", tiles, False, 34, DISPLAY_HEIGHT)
    display_text(screen, str(thx.enmax) + "\\", tiles, False, 34, DISPLAY_HEIGHT + 2)
    
    shield = thx.shield()
    if shield:
        bar_width = tile_size * DISPLAY_WIDTH * shield / THX_SHIELD_STRENGTH
        screen.fill(COLORS[0x05], pygame.Rect((tile_size * DISPLAY_WIDTH - bar_width)/2, tile_size * (DISPLAY_HEIGHT + 1) + PX_SIZE, bar_width, PX_SIZE * (TILE_HEIGHT - 1)))
    else:
        display_text(screen, "SHIELD OFF", tiles, False, (DISPLAY_WIDTH - 10) / 2, DISPLAY_HEIGHT + 1)
    
    draw_health_bar(screen, thx.get_health())
    
def draw_health_bar(screen, health):
    """
    This is pretty clear what this does. It takes as input the health and fills in a health bar
    appropriately coloured.
    """        
    if health > 40: # green
        if health > 100:
            health = 100
        screen.fill(COLORS[0x02], pygame.Rect(18 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 2) * PX_SIZE, PX_SIZE * TILE_WIDTH * (health - 40)/4, PX_SIZE * 5))
        health = 40
    if health > 20: # yellow
        screen.fill(COLORS[0x06], pygame.Rect(13 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 2) * PX_SIZE, PX_SIZE * TILE_WIDTH * (health - 20)/4, PX_SIZE * 5))
        health = 20

    # ... and red.
    screen.fill(COLORS[0x05], pygame.Rect(8 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 2) * PX_SIZE, PX_SIZE * TILE_WIDTH * (health)/4, PX_SIZE * 5))

    # Now draw the border.
    screen.fill(COLORS[0x0f], pygame.Rect(8 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 1) * PX_SIZE,
            PX_SIZE * TILE_WIDTH * 25, PX_SIZE))
    screen.fill(COLORS[0x0f], pygame.Rect(8 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 7) * PX_SIZE,
            PX_SIZE * TILE_WIDTH * 25, PX_SIZE))
    screen.fill(COLORS[0x0f], pygame.Rect(8 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 1) * PX_SIZE,
            PX_SIZE, PX_SIZE * 7))
    screen.fill(COLORS[0x0f], pygame.Rect(33 * PX_SIZE * TILE_WIDTH, (DISPLAY_HEIGHT * TILE_HEIGHT + 1) * PX_SIZE,
            PX_SIZE, PX_SIZE * 7))

        
def display_tile(screen, tile, x, y):
    """
    This draws a tile at screen location (x, y)---not pixel location.
    
    This is the main method for drawing any tiles on the screen.
    """
    tile_size = PX_SIZE * TILE_HEIGHT

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

def display_sprites(screen, level, sprites, frame_number, x, y):

    #monsters = level.monsters()

    for monst in sprites:
        if monst != THX_SPRITE:
            sprite = sprites[monst]
            pos = sprite.get_pos()
            if (x - 1 <= pos[0]< x + DISPLAY_WIDTH) and (y - 1 <= pos[1]< y + DISPLAY_HEIGHT):
                # This is just so that each sprite type can have its own way of determining
                # which frame to show.
                cur_frame = sprites[monst].frame_no(frame_number)
                
                display_tile(screen, level.monster_data(sprite.monster_type()).tile(cur_frame),
                        pos[0] - x, pos[1] - y)


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
        if monst != THX_SPRITE:
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
    

def target_hit(level, sprites, x, y):
    """
    This should tell you what is at the location (x, y) in case you hit it.
    """
    hit_tile = level.tile(x, y)
    if hit_tile:
    
        # TODO: Sort out exactly which tiles we can destroy. In most levels, 0x0d is correct.
        
        return (0, x, y, hit_tile)
        
    monst = sprite_collision(sprites, -1, animation.frame(x,y,1,1))
    if monst:
        # Monsters are killable!
        if sprites[monst].zap() <= 0:
        
            ident = sprites[monst].monster_type()
            
            del sprites[monst]
            
            return (1, ident, monst)

        return monst
                    
    return False


##################################################################################################
#
# End display methods.
#
##################################################################################################

# TODO: There is a bug here, in that when you are falling near the top of the level and firing
#       the laser at the same time, it comes from the wrong spot.



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
    
    sprites = levels[curlvl].monsters().copy()
    
    sprites[THX_SPRITE] = robot.Robot()
    
    #thx = robot.Robot()
    
    thx = sprites[THX_SPRITE]


    (lower_tile, upper_tile) = tile_bounds()

    #t2 = time.time()
    #print "%f seconds\n" % (t2 - t1)

    tile_size = PX_SIZE * TILE_HEIGHT

    screen = display_init(DISPLAY_WIDTH * tile_size, SCREEN_HEIGHT * tile_size)
#    screen = display_init(DISPLAY_WIDTH * tile_size, DISPLAY_HEIGHT * tile_size)

    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

    x_pos = 0
    y_pos = 0

    # This will just allow us to toggle between noclip/clipping for debug.
    clipping = True

    game_clock = 0

    pygame.time.set_timer(TIME_EVENT, FRAME_LENGTH_MS)

    going = True
    while going:

        y_pos = thx.y() - 11
        if y_pos < 0:
            y_pos = 0
        elif y_pos > LVL_HEIGHT - DISPLAY_HEIGHT:
            y_pos = LVL_HEIGHT - DISPLAY_HEIGHT

        x_pos = thx.x() - 19
        if x_pos < 0:
            x_pos = 0

        display_level(screen, levels[curlvl], lvl_graphics, x_pos, y_pos)
        display_sprites(screen, levels[curlvl], sprites, game_clock % NUM_TILES, x_pos, y_pos)
        display_tile(screen, thx.tile(), 19, thx.y() - y_pos)
        
        display_stats(screen, lvl_tiles, thx)
    
        
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

                    sprites = levels[curlvl].monsters().copy()
                    sprites[THX_SPRITE] = thx

                    thx.set_x(19)
                    thx.set_y(11)
                elif keys[K_n]:
                    curlvl -= 1
                    if curlvl < 0:
                        curlvl = 0

                    (lower_tile, upper_tile) = tile_bounds(curlvl)
                    lvl_graphics = lvl_tiles[lower_tile:upper_tile]

                    sprites = levels[curlvl].monsters().copy()
                    sprites[THX_SPRITE] = thx

                    thx.set_x(19)
                    thx.set_y(11)
                elif keys[K_r]:
                    # This should load and display the thexder robot animation. 
                    #show_tiles(screen, lvl_tiles)
                    for i in range(0, 0x10):
                        for j in range(0, 0x20):
                            if (j * 0x10 + i) < len(lvl_tiles):
                                display_text(screen, chr(j * 0x10 + i), lvl_tiles, False, i , j)
                    pygame.display.update()
                    pause()
                elif keys[K_c]:
                    clipping = not clipping
                elif keys[K_z]:
                    thx.shield_on()
                    
                #elif keys[K_t]:
                    # I still want to be able to look over the enemy tiles, since this seems to be an issue...
                #    view_enemies(screen, levels[curlvl])
                else:
                    pass

# TODO: I also need to work out how to change between the different robot states better.

            elif event.type == TIME_EVENT:
            
                if thx.is_dead():
                    pass
                    
                game_clock += 1
            
                move_monsters(levels[curlvl], sprites, x_pos, game_clock)
                
                thx.tick()
                
                if thx.wait():
                
                    # While transforming, nothing should happen.
                    
                    pass
                elif thx.is_robot():
                
                    keys = pygame.key.get_pressed()
                    
                    if thx.is_jumping():
                        if keys[K_UP] and thx.jump() and is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping):
                            thx.set_y(thx.y() - 1)
                        else:
                            if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping):
                                thx.fall()
                                thx.set_y(thx.y() + 1)
                            else:
                                thx.land()
                    elif thx.is_falling():
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping):
                            thx.set_y(thx.y() + 1)
                        else:
                            thx.land()
                    elif thx.is_grounded():
                        if keys[K_UP] and is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping):
                            thx.jump()
                            thx.set_y(thx.y() - 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping):
                            thx.fall()
                            thx.set_y(thx.y() + 1)


                    if keys[K_DOWN]:
                        thx.transform()
                    elif keys[K_RIGHT]:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().E(), clipping):
                            thx.set_x(thx.x() + 1)
                        thx.push_direction(DIR_E)
                        if thx.is_grounded():
                            thx.step()
                    elif keys[K_LEFT]:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().W(), clipping):
                            thx.set_x(thx.x() - 1)
                        thx.push_direction(DIR_W)
                        if thx.is_grounded():
                            thx.step()
                    
                    
                    # TODO: Something funny here when jumping/falling... 
                         
                    if keys[K_SPACE]:
                        thx.fire()

                        if thx.direction() == DIR_E:
                            targets = get_laser_targets(sprites, x_pos, y_pos, True)

                            if len(targets):
                                target = targets[game_clock % len(targets)]
                                laser_dir = (target[0] - (thx.x() + 2), target[1] - thx.y())
                            else:
                                laser_dir = (1,0)
                                
                            result = draw_laser(screen, 20, robot_screen_y_pos(thx.y()), laser_dir, (1,0))
                            
                            if result:
                                hit = target_hit(levels[curlvl], sprites, result[0] + x_pos, result[1] + y_pos)
                                
                                if hit:
                                    if type(hit) is tuple:
                                        if hit[0] == 0:
                                            if hit[3] in SHOOTABLE_TILES[curlvl]:
                                                levels[curlvl].map.change_tile(hit[1], hit[2], 0x00)
                                        else:
                                            thx.kill(levels[curlvl].monster_data(hit[1]))
                        else:
                            targets = get_laser_targets(sprites, x_pos, y_pos, False)
                            
                            if len(targets):
                                target = targets[game_clock % len(targets)]
                                laser_dir = (target[0] - thx.x(), target[1] - thx.y())
                            else:
                                laser_dir = (-1,0)
                                
                            result = draw_laser(screen, 20, robot_screen_y_pos(thx.y()), laser_dir, (-1,0))
                            
                            if result:
                                hit = target_hit(levels[curlvl], sprites, result[0] + x_pos, result[1] + y_pos)

                                if hit:
                                    if type(hit) is tuple:
                                        if hit[0] == 0:
                                            if hit[3] in SHOOTABLE_TILES[curlvl]:
                                                levels[curlvl].map.change_tile(hit[1], hit[2], 0x00)
                                        else:
                                            thx.kill(levels[curlvl].monster_data(hit[1]))

                    if thx.is_robot():
                        # Check to see if the ground below us damages the robot.
                        take_damage = False
                        for row in levels[curlvl].tiles(thx.get_frame().S()):
                            if DAMAGE_TILE in row:
                                take_damage = True
                                break
                        if take_damage:
                            thx.take_damage()
                                

                else:
                    thx_blocked = False # Start by assuming that the jet is not blocked in its direction
                                        # of motion. If it turns out to be, then it should try transform.
                    
                    keys = pygame.key.get_pressed()

# TODO: Fix the up/down thing when in a tunnel.

                    if keys[K_UP] and keys[K_LEFT]:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NW(), clipping):
                            thx.push_direction(DIR_NW)
                    elif keys[K_UP] and keys[K_RIGHT]:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NE(), clipping):
                            thx.push_direction(DIR_NE)
                    elif keys[K_DOWN] and keys[K_LEFT]:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SW(), clipping):
                            thx.push_direction(DIR_SW)
                    elif keys[K_DOWN] and keys[K_RIGHT]:                    
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SE(), clipping):
                            thx.push_direction(DIR_SE)
                    elif keys[K_UP]:
                        thx.push_direction(DIR_N)
                    elif keys[K_DOWN]:
                        thx.push_direction(DIR_S)
                    elif keys[K_LEFT]:
                        if thx.direction() == DIR_E and (is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping) or is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping)):
                            thx_blocked = True
                        else:
                            thx.push_direction(DIR_W)
                    elif keys[K_RIGHT]:
                        if thx.direction() == DIR_W and (is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping) or is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping)):
                            thx_blocked = True
                        else:
                            thx.push_direction(DIR_E)

                    direction = thx.direction()
                    if direction == DIR_E:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().E(), clipping):
                            thx.set_x(thx.x() + 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NE(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.set_y(thx.y() - 1)
                            thx.push_direction(DIR_NE)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SE(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.set_y(thx.y() + 1)
                            thx.push_direction(DIR_SE)
                        else:
                            thx_blocked = True
                    elif direction == DIR_W:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().W(), clipping):
                            thx.set_x(thx.x() - 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NW(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.set_y(thx.y() - 1)
                            thx.push_direction(DIR_NW)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SW(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.set_y(thx.y() + 1)
                            thx.push_direction(DIR_SW)
                        else:
                            thx_blocked = True
                    elif direction == DIR_N:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping):
                            thx.set_y(thx.y() - 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NW(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.set_y(thx.y() - 1)
                            thx.push_direction(DIR_NW)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NE(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.set_y(thx.y() - 1)
                            thx.push_direction(DIR_NE)
                        else:
                            thx_blocked = True
                    elif direction == DIR_S:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping):
                            thx.set_y(thx.y() + 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SW(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.set_y(thx.y() + 1)
                            thx.push_direction(DIR_SW)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SE(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.set_y(thx.y() + 1)
                            thx.push_direction(DIR_SE)
                        else:
                            thx_blocked = True

                    # Diagonals
                    elif direction == DIR_NW:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NW(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.set_y(thx.y() - 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().W(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.push_direction(DIR_W)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping):
                            thx.set_y(thx.y() - 1)
                            thx.push_direction(DIR_N)
                        else:
                            thx_blocked = True
                    elif direction == DIR_NE:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().NE(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.set_y(thx.y() - 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().E(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.push_direction(DIR_E)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().N(), clipping):
                            thx.set_y(thx.y() - 1)
                            thx.push_direction(DIR_N)
                        else:
                            thx_blocked = True
                    elif direction == DIR_SE:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SE(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.set_y(thx.y() + 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().E(), clipping):
                            thx.set_x(thx.x() + 1)
                            thx.push_direction(DIR_E)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping):
                            thx.set_y(thx.y() + 1)
                            thx.push_direction(DIR_S)
                        else:
                            thx_blocked = True
                    elif direction == DIR_SW:
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().SW(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.set_y(thx.y() + 1)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().W(), clipping):
                            thx.set_x(thx.x() - 1)
                            thx.push_direction(DIR_W)
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, thx.get_frame().S(), clipping):
                            thx.set_y(thx.y() + 1)
                            thx.push_direction(DIR_S)
                        else:
                            thx_blocked = True
                    
                    if keys[K_SPACE]:
                        thx.fire()
                        
                        direction = dir_to_vec(thx.facing())
                        result = draw_laser(screen, 20, robot_screen_y_pos(thx.y()) + 1, direction, direction)

                        if result:
                            hit = target_hit(levels[curlvl], sprites, result[0] + x_pos, result[1] + y_pos)

                            if hit:
                                if type(hit) is tuple:
                                    if hit[0] == 0:
                                        if hit[3] in SHOOTABLE_TILES[curlvl]:
                                            levels[curlvl].map.change_tile(hit[1], hit[2], 0x00)
                                    else:
                                        thx.kill(levels[curlvl].monster_data(hit[1]))

                    
                    if thx_blocked:
                        # Try transform; if you can't, then turn around.
                        big_frame = animation.frame(thx.x(), thx.y(), thx.width(), thx.height() + 1)
                        if is_empty(levels[curlvl], sprites, THX_SPRITE, big_frame, clipping):
                            thx.transform()
                        elif is_empty(levels[curlvl], sprites, THX_SPRITE, big_frame.N(), clipping):
                            thx.set_y(thx.y() - 1)
                            thx.transform()
                        else:
                            # TODO: This seems a little off in timing?
                            if thx.direction() == DIR_E:
                                thx.push_direction(DIR_W)
                                thx.set_x(thx.x() - 1)
                            elif thx.direction() == DIR_W:
                                thx.push_direction(DIR_E)
                                thx.set_x(thx.x() + 1)

                if thx.y() < 0:
                    thx.set_y(0)
                if thx.y() > LVL_HEIGHT - 4: # This is a little cheeky, since for a plane you 
                                             # _technically_ could be lower than this...
                    thx.set_y(LVL_HEIGHT - 4)
                    
                    
##############################


def cli():
    config.set_app_config_from_cli(config.base_argument_parser())
    return main()

if __name__ == "__main__":
    cli()
