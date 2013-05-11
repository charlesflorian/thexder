from constants import *
from . import animation
from . import data
from . import level

#################################################################################################
#
# The ROBOT.BIN file consists of a bunch of frames, in the following order:
#
# 0x00--0x07:   Running left
# 0x08--0x0f:   Running right
# 0x10:         Landing left
# 0x11:         Landing right
# 0x12:         Turning (facing left)
# 0x13:         Turning (facing right)
# 0x14--0x15:   Transforming stage 1, 2 (left)
# 0x16--0x17:   Transforming stage 1, 2 (right)
#
# All of which are 3 x 4 frames. Then it has number of 3 x 3 frames which are flying frames.
#
# 0x00--0x03:   Transforming stage 3--6 (left)
# 0x04--0x07:   Transforming stage 3--6 (right)
#
# The next 16 frames are the 16 possible directions that the robot can fly in.
#
# Lastly, there are frames of the robot dying.
#
#######################################################################

# The goal is to have a collection of "reels" i.e. of lists of frames. Then when we are supposed
# to go from state A->B we find our place in the reel and return frames along it...

THX_FLYING_ANIM = [0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e,0x2f]
THX_WALKING_RIGHT_ANIM = [0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f]
THX_WALKING_LEFT_ANIM = [0x0,0x01,0x02,0x03,0x04,0x05,0x06,0x07]
THX_TRANSFORMING_RIGHT_ANIM = [0x16,0x17,0x1c,0x1d,0x1e,0x1f]
THX_TRANSFORMING_LEFT_ANIM = [0x14,0x15,0x18,0x19,0x1a,0x1b]
THX_TURNING_ANIM = [0x11,0x12]

THX_SAME_DIR = 0x100

class rState(object):
    def __init__(self, direction=THX_SAME_DIR, flags=0):
        self.direction = direction
        self.flags = flags

class Robot(object):
    """
    This will be the class of the Thexder robot. It will include the animation tiles for him,
    at the very least.
    """
    global THX_GROUNDED, THX_FALLING, THX_JUMPING

    def __init__(self, filename="ROBOT.BIN"):   
        global TILE_WIDTH, TILE_HEIGHT

        global THX_GROUNDED, THX_FALLING, THX_JUMPING
        content = data.default_data_manager().load_file(filename)

        # The number of bits per frame.
        big_frame_bits = 3 * 4 * TILE_HEIGHT * TILE_WIDTH /2
        small_frame_bits = 3 * 3 * TILE_HEIGHT * TILE_WIDTH /2

        # This separates it into the large and small frames, which will be processed separately.
        big_frames_raw = content[:big_frame_bits * 0x18]
        small_frames_raw = content[big_frame_bits * 0x18:]

        # And now we make them into a bunch of tiles.
        self.big_frames = []
        for i in range(0, len(big_frames_raw) / big_frame_bits):
            self.big_frames.append(animation.Tile(big_frames_raw, i * big_frame_bits, 3 * TILE_WIDTH, 4 * TILE_HEIGHT))

        self.small_frames = []
        for i in range(0, len(small_frames_raw) / small_frame_bits):
            self.small_frames.append(animation.Tile(small_frames_raw, i * small_frame_bits, 3 * TILE_WIDTH, 3 * TILE_HEIGHT))

        # Collect the frames for the transformation sequence together.
        self.transform_frames = []
        self.transform_frames.extend(self.big_frames[0x14:0x16])
        self.transform_frames.extend(self.small_frames[0x00:0x04])
        self.transform_frames.extend(self.big_frames[0x16:0x18])
        self.transform_frames.extend(self.small_frames[0x04:0x08])

        self.left_facing = False
        self.frame_no = 0
        self.turning = False
        self.jump_height = 0

        self.state = THX_GROUNDED

        self.enmax = 100
        self.heatlh = 100

        self.transition_frame = 0

        self.jet = False
        
        
        # NEW STUFF
        
        self.frames = self.big_frames
        self.frames.extend(self.small_frames)
        self.step_count = 0
        self.reel = []
        self.thx_state = rState(DIR_E, THX_FLAG_ROBOT)

# Animations.

    def get_frame(self):
        if self.is_transforming():
        
            if self.is_jet():
                if self.is_facing_left():
                    return self.transform_frames[self.transition_frame].tile()
                else:
                    return self.transform_frames[6 + self.transition_frame].tile()
            else:
                if self.is_facing_left():
                    return self.transform_frames[5 - self.transition_frame].tile()
                else:
                    return self.transform_frames[11 - self.transition_frame].tile()
                    
        elif self.is_jet():
            return self.get_plane_animation()[self.state].tile()
        elif self.is_jumping():
            if self.is_facing_left():
                return self.big_frames[0x06].tile()
            else:
                return self.big_frames[0x0a].tile()
        elif self.is_turning():
            if self.is_facing_left():
                return self.big_frames[0x13 - self.transition_frame].tile()
            else:
                return self.big_frames[0x12 + self.transition_frame].tile()
        else:
            if self.left_facing:
                return self.get_left_animation()[self.frame_no].tile()
            else:
                return self.get_right_animation()[self.frame_no].tile()

# TODO: Make this only have to do with walking, and nothing else.

    def step(self):
        self.frame_no += 1
        if self.frame_no >= 8:
            self.frame_no = 0

# Actions

    def transform(self):
        self.set_state(THX_TRANSFORMING)
        self.transition_frame = 0
        self.jump_height = 0
        self.jet = not self.jet

    def set_jumping(self, status):
        self.jump_height = status

    def jump(self):
        global JUMP_MAX_HEIGHT, THX_JUMPING
        self.state = THX_JUMPING
        self.jump_height += 1
        if self.jump_height > JUMP_MAX_HEIGHT:
            self.jump_height = 0
        return self.jump_height

    def turn(self):
        #self.frame_no = 0
        self.left_facing = not self.left_facing
        self.turning = True

    def fall(self):
        self.frame_no = 0
        self.state = THX_FALLING

    def land(self):
        self.state = THX_GROUNDED
        self.jump_height = 0

    def set_state(self, state):
        if self.is_jet():
            self.state = state
            if state > THX_FLYING_N and state < THX_FLYING_S:
                self.left_facing = False
# This is a little bit kludge-y. I'm not sure if I like this, but it's my own fault for using .state to refer to as many things as I
# am.
            elif (state < THX_FLYING_N or state > THX_FLYING_S) and state < THX_TRANSFORMING:
                self.left_facing = True
        else:
            if state == THX_FALLING:
                pass
            self.state = state



    def update(self):
#        if self.is_jet():
#            pass
#        elif self.get_state() == THX_TRANSFORMING:
        if self.get_state() == THX_TRANSFORMING:
            self.transition_frame += 1
            if self.transition_frame >= 6:
                self.transition_frame = 0
                if self.is_jet():
                    if self.is_facing_left():
                        self.set_state(THX_FLYING_W)
                    else:
                        self.set_state(THX_FLYING_E)
                else:
                    self.set_state(THX_FALLING)
        elif self.is_turning():
            self.transition_frame += 1
            if self.transition_frame >= 2:
                self.turning = False
                self.transition_frame = 0
            

# Queries:
    def is_turning(self):
        return self.turning


    def is_jet(self):
        return self.jet

    def is_facing_left(self):
        return self.left_facing

    def is_grounded(self):
        return self.get_state() == THX_GROUNDED

    def is_transforming(self):
        return self.get_state() == THX_TRANSFORMING

    def is_jumping(self):
        return self.get_state() == THX_JUMPING

    def get_state(self):
        return self.state


# A State should consist of a direction and some flags

# New interface
    def direction(self):
        return self.query_state().direction
        
    def flags(self):
        return self.query_state().flags
        
    def is_robot(self):
        return self.flags() & THX_FLAG_ROBOT

    def step(self):
        self.step_count += 1
        if self.step_count >= 8:
            self.step_count = 0

    def frame(self):
        if len(self.reel):                   # If there is a current animation...
            return self.frames[self.reel[0]].tile() # ... use that frame.
        else:
            # Return whatever other frame we should use.
            # This will require a bit of work.
            
            # Things to consider: Robot/non-robot? Left/right?
            if not self.is_robot(): 
                return self.frames[THX_FLYING_FRAMES + self.direction()].tile()
            else:
                if self.direction() == DIR_E:
                    return self.frames[0x08].tile()
                else:
                    return self.frames[0].tile()
        
        
    def tick(self):
        if len(self.reel):
            self.reel.pop(0) # This just knocks off one frame in the animation.
                
    def push_state(self, state):
        if state.flags & THX_FLAG_JET and self.is_robot(): # Transform to jet
            if self.direction() == DIR_E:
                self.reel = THX_TRANSFORMING_RIGHT_ANIM
            else:
                self.reel = THX_TRANSFORMING_LEFT_ANIM
            self.thx_state = rState(self.direction(), THX_FLAG_JET)
        elif state.flags & THX_FLAG_ROBOT and not self.is_robot(): # Transform to robot
        
            # TODO: This is not quite right. It should 'remember' the previous direction (E/W) you were flying
            #       and use that to choose the new direction when you are going up/down. But this is close.
            
            if DIR_N < self.direction() <= DIR_S:
                self.reel = THX_TRANSFORMING_RIGHT_ANIM.reverse()
                direction = DIR_E
            else:
                self.reel = THX_TRANSFORMING_LEFT_ANIM.reverse()
                direction = DIR_W
            self.thx_state = rState(direction, THX_FLAG_ROBOT & THX_FLAG_FALL)
        
        # TODO: Add direction change.
        # TODO: Add landing.
        # TODO: Add direction change if in jet form.
        
    def query_state(self):
        return self.thx_state
        

# These are probably only needed for debugging.
    def get_left_animation(self):
        """
        For now, all of these simply return the portion of the array of frames which correspond to the desired animation.
        This should probably be wrapped in an animation class.
        """
        return self.big_frames[0x00:0x08]

    def get_right_animation(self):
        return self.big_frames[0x08:0x10]

    def get_plane_animation(self):
        return self.small_frames[0x08:0x18]
