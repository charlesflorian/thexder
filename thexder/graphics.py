import pygame
from pygame.locals import *

from constants import *

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
            output.fill(COLORS[tile[i][j]], pygame.Rect(j*px_size,i*px_size,(j+1)*px_size,(i+1)*px_size))

    return output


