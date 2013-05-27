from random import randint

from . import animation

from constants import *

def collision(frame_1, frame_2):
    if frame_1.x + frame_1.width <= frame_2.x:
        return False
    if frame_1.x >= frame_2.x + frame_2.width:
        return False
    if frame_1.y + frame_1.height <= frame_2.y:
        return False
    if frame_1.y >= frame_2.y + frame_2.height:
        return False
    return True

def sprite_collision(monsters, monster_id, new_frame):
    for monst in monsters:
        if monster_id != monsters[monst].get_ident():
            if collision(monsters[monst].get_frame(), new_frame):
                return monst
    return False

def robot_empty(level, frame):
    if not level.is_empty(frame.x, frame.y, frame.width, frame.height):
        return False
    if sprite_collisions(level.monsters(), -1, frame):
        return False
    return True
        

def is_empty(level, monsters, monst_ident, frame, robot_x, robot_y, is_robot=True):
    """
    This just checks to see if there is anything where we are trying to go. This should be the default
    method to look for stuff.
    """
    if level.is_empty(frame.x, frame.y, frame.width, frame.height):
        if is_robot:
            robot_frame = animation.frame(robot_x, robot_y, 3, 4)
        else:
            robot_frame = animation.frame(robot_x, robot_y, 3, 3)
        if not sprite_collision(monsters, monst_ident, frame) and not collision(frame, robot_frame):
            return True
    return False

# TODO: Fix the monster motion. If they hit a wall for at lest one tick and they
#       COULD be moving the other way, they should switch? Something like that...

def monster_move(level, monsters, monst, robot_x, robot_y, clock, is_robot=True):
    """
    This is the function which will take as input some data (including the motion type)
    and return the new coordinates based on that input.
    """    
    
    pos = monst.get_pos()
    old_x = pos[0]
    old_y = pos[1]

    new_x = old_x
    new_y = old_y
    
    motion_type = monst.get_motion()
    
    if motion_type == 0x00:
        pass
    elif motion_type == 0x01: # Normal slow flying
        # TODO: Fix this. It should involve the state of the sprite.
        state = monst.get_state()
        if old_x > robot_x + 3 and old_y < robot_y:
            monst.set_state(0)
        elif old_x > robot_x + 3 and old_y > robot_y + 4:
            monst.set_state(1)
        elif old_x < robot_x and old_y < robot_y:
            monst.set_state(2)
        elif old_x < robot_x and old_y > robot_y + 4:
            monst.set_state(3)

        state = monst.get_state()
        if state == 0:
            new_frame = animation.frame(old_x - 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y + 1
#            else:
#                monst.set_state(1)
        if state == 1:
            new_frame = animation.frame(old_x - 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y - 1
#            else:
#                monst.set_state(0)
        if state == 2:
            new_frame = animation.frame(old_x + 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y + 1
#            else:
#                monst.set_state(3)
        if state == 3:
            new_frame = animation.frame(old_x + 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y - 1
#            else:
#                monst.set_state(2)

    elif motion_type == 0x02: # Falling
        new_x = old_x
        new_frame = animation.frame(old_x, old_y + 1, 2, 2)
        if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
            new_y = old_y + 1
        else:
            new_y = old_y
    elif motion_type == 0x03: # Slow horizontal motion, no falling.
        if clock % 2:
            if robot_x < old_x - 1:
                new_frame = animation.frame(old_x - 1, old_y, 2, 2)
                if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                    new_x = old_x - 1
            elif robot_x > old_x:
                new_frame = animation.frame(old_x + 1, old_y, 2, 2)
                if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                    new_x = old_x + 1
    elif motion_type == 0x04: # Rocket-type loopy motion
    
        # TODO: Make them actually try to follow you!        
        
        state = monst.get_state()
        
        if state == 0:
            new_frame = animation.frame(old_x - 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y + 1
            monst.set_state(1)
        elif state == 1:
            new_frame = animation.frame(old_x - 1, old_y, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
            monst.set_state(2)
        elif state == 2:
            new_frame = animation.frame(old_x - 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y - 1
            monst.set_state(3)
        elif state == 3:
            new_frame = animation.frame(old_x, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_y = old_y - 1
            monst.set_state(4)
        elif state == 4:
            new_frame = animation.frame(old_x + 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y - 1
            monst.set_state(5)
        elif state == 5:
            new_frame = animation.frame(old_x + 1, old_y, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
            monst.set_state(6)
        elif state == 6:
            new_frame = animation.frame(old_x + 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y + 1
            monst.set_state(7)
        elif state == 7:
            new_frame = animation.frame(old_x, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_y = old_y + 1
            monst.set_state(0)
        
    elif motion_type == 0x05: # Falls, then moves slowly, possibly to the left/right depending on position.
        if clock % 2:
            # Check downward motion first.
            new_frame = animation.frame(old_x, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_y += 1
            else:
                if robot_x + 2 < old_x:
                    monst.set_state(0)
                elif robot_x > old_x:
                    monst.set_state(1)
                    
                state = monst.get_state()            
                if state == 0:
                    new_frame = animation.frame(old_x - 1, old_y, 2, 2)
                    if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                        new_x = old_x - 1
                    else:
                        monst.set_state(1)
                elif state == 1:
                    new_frame = animation.frame(old_x + 1, old_y, 2, 2)
                    if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                        new_x = old_x + 1
                    else:
                        monst.set_state(0)
            

    elif motion_type == 0x06: #       06 - hidden (animation is different!), no moving once open.
        pass
    elif motion_type == 0x07: #       07 - hidden (animation is different!), moves quickly once open.
    
        # TODO: This will eventually need an interaction  method; it is hidden until...
        
#        if monst.get_state() == 3:
        if monst.get_state() == 0:
            if old_x < robot_x:
                new_frame = animation.frame(old_x + 1, old_y, 2, 2)
                if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                    new_x = old_x + 1
            elif old_x > robot_x:
                new_frame = animation.frame(old_x - 1, old_y, 2, 2)
                if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                    new_x = old_x - 1
    elif motion_type == 0x08: #       08 - falls, moves randomly-ish.
        new_x = old_x
        new_frame = animation.frame(old_x, old_y + 1, 2, 2)
        if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
            new_y = old_y + 1
        else:
            if randint(0,1) == 0:
                new_frame = animation.frame(old_x - 1, old_y, 2, 2)
                if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                    new_x = old_x - 1
            else:
                new_frame = animation.frame(old_x + 1, old_y, 2, 2)
                if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                    new_x = old_x + 1
    elif motion_type == 0x09: #       09 - Seems to be about the same as 04?
        pass                  # It is worth noting that this motion type does not actually occur in the bugdb
                              # files anywhere...
                             
    elif motion_type == 0x0a: #       0A - Quick up/down flying (ala bats)
        # TODO: The bottom part of this motion is not quite right.

        if old_x > robot_x + 3 and old_y < robot_y:
            monst.set_state(0)
        elif old_x > robot_x + 3 and old_y >= robot_y + 3:
            monst.set_state(1)
        elif old_x < robot_x and old_y < robot_y:
            monst.set_state(2)
        elif old_x < robot_x and old_y >= robot_y + 3:
            monst.set_state(3)

        state = monst.get_state()
        if state == 0:
            new_frame = animation.frame(old_x - 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y + 1
        if state == 1:
            new_frame = animation.frame(old_x - 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y - 1
        if state == 2:
            new_frame = animation.frame(old_x + 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y + 1
        if state == 3:
            new_frame = animation.frame(old_x + 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y - 1

    elif motion_type == 0x0b: #       0B - Weird jittery flying (also fast)
        if old_x > robot_x + 3 and old_y < robot_y:
            monst.set_state(0)
        elif old_x > robot_x + 3 and old_y >= robot_y:
            monst.set_state(1)
        elif old_x < robot_x and old_y < robot_y:
            monst.set_state(2)
        elif old_x < robot_x and old_y >= robot_y:
            monst.set_state(3)

        state = monst.get_state()
        if state == 0:
            new_frame = animation.frame(old_x - 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y + 1
        if state == 1:
            new_frame = animation.frame(old_x - 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x - 1
                new_y = old_y - 1
        if state == 2:
            new_frame = animation.frame(old_x + 1, old_y + 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y + 1
        if state == 3:
            new_frame = animation.frame(old_x + 1, old_y - 1, 2, 2)
            if is_empty(level, monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
                new_x = old_x + 1
                new_y = old_y - 1
    else: #       >= 0C - diagonal fall, then no moving.
        new_frame = animation.frame(old_x - 1, old_y + 1, 2, 2)
        if is_empty(level,monsters, monst.get_ident(), new_frame, robot_x, robot_y, is_robot):
            new_x = old_x - 1
            new_y = old_y + 1

    return (new_x, new_y)


def move_monsters(level, screen_x, screen_y, robot_x, robot_y, clock):
    """    
    This just moves all of the monsters using the previous method.
    """
    monsters = level.monsters()
    
    for monst in monsters:
        
        monst_pos = monsters[monst].get_pos()
        
        if screen_x - 1 < monst_pos[0] < screen_x + DISPLAY_WIDTH:
            # We only want to moves monsters within the display's width (any y-position, though).
             
            (new_x, new_y) = monster_move(level, monsters, monsters[monst], robot_x, robot_y, clock)
            
            monsters[monst].move_to(new_x, new_y)

