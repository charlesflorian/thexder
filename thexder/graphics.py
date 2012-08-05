import pygame
from pygame.locals import *

from constants import *

def render_lvl_tiles(tiles, lower, upper):
    """
    This should take as input a set of tiles and return as output an array of game tiles. These
    will be pygame.Surface objects.
    """
    
    output = []

    for k in range(lower, upper):
        output.append(render_tile(tiles[k],2))

    output.append(pygame.Surface((16,16)))

    # Make the last one a blank one.
    pygame.draw.rect(output[len(output) - 1],(180,0,0),(0,0,16,16),0)

    # This is just so that I can (tentatively) draw monsters.
    output.append(pygame.Surface((16,16)))
    pygame.draw.rect(output[len(output) - 1],(255,75,150),(0,0,16,16),0)

    return output


def render_tile(tile, px_size = 20):
    """
    This just draws a tile onto a new pygame.Surface object, and returns that object.

    The surface object it returns is automatically the correct size.

    The input is a list of lists, i.e. a two dimensional array consisting of the pixel data.
    """
    width = len(tile[0])
    height = len(tile)
    output = pygame.Surface((px_size * width, px_size * height))
    for i in range(0, height):
        for j in range(0, width):
            pygame.draw.rect(output,COLORS[tile[i][j]],(j*px_size,i*px_size,(j+1)*px_size,(i+1)*px_size),0)

    return output


