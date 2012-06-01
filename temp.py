from curses import *
from math import *
from random import *
from sys import exit
from os import rename
#import pygame
#from pygame.locals import *


def init_colours():
    init_pair(1,COLOR_BLACK,COLOR_BLACK)
    init_pair(2,COLOR_RED,COLOR_BLACK)
    init_pair(3,COLOR_GREEN,COLOR_BLACK)
    init_pair(4,COLOR_YELLOW,COLOR_BLACK)
    init_pair(5,COLOR_BLUE,COLOR_BLACK)
    init_pair(6,COLOR_MAGENTA,COLOR_BLACK)
    init_pair(7,COLOR_CYAN,COLOR_BLACK)
    init_pair(8,COLOR_WHITE,COLOR_BLACK)
    init_pair(10,COLOR_BLACK,COLOR_BLACK)
    init_pair(11,COLOR_BLACK,COLOR_RED)
    init_pair(12,COLOR_BLACK,COLOR_GREEN)
    init_pair(13,COLOR_BLACK,COLOR_YELLOW)
    init_pair(14,COLOR_BLACK,COLOR_BLUE)
    init_pair(15,COLOR_BLACK,COLOR_MAGENTA)
    init_pair(16,COLOR_BLACK,COLOR_CYAN)
    init_pair(17,COLOR_BLACK,COLOR_WHITE)


def main(w):
    f = open("TANBIT03.BIN","rb")
    f.read(0x1c00)
    v = f.read(1)
    
    
wrapper(main)
