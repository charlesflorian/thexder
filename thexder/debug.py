import pygame
from pygame.locals import *


from constants import *

################################################################################################## 
#
# Debug stuff.
#
##################################################################################################

def show_tiles(screen, tileset, anim=False):
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

