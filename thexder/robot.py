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

# Animations.

    def get_frame(self):
        if self.is_transforming():    
            if self.is_facing_left():
                if self.is_jet():
                    return self.transform_frames[self.transition_frame].tile()
                else:
                    return self.transform_frames[6 - self.transition_frame].tile()
            else:
                if self.is_jet():
                    return self.transform_frames[6 + self.transition_frame].tile()
                else:
                    return self.transform_frames[12 - self.transition_frame].tile()
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

# TODO: Make this run the animation
    def transform(self):
        self.set_state(THX_TRANSFORMING)
        self.transition_frame = 0
        self.jump_height = 0
        self.jet = not self.jet
#        if self.is_jet():  
#            self.jet = False
#            self.set_state(THX_FALLING)
#            self.jump_height = 0
#        else:
#            self.jump_height = 0
#            self.jet = True
#            if self.is_facing_left():
#                self.set_state(THX_FLYING_W)
#            else:
#                self.set_state(THX_FLYING_E)


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
            elif state < THX_FLYING_N or state > THX_FLYING_S:
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
