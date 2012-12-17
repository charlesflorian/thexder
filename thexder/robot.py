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

        self.flying = False
        self.left_facing = False
        self.frame_no = 0
        self.turning = False
        self.grounded = True
        self.transforming = False
        self.jumping = 0

        self.state = THX_GROUNDED

        self.enmax = 100
        self.heatlh = 100

# Animations.
    def get_frame(self):
        if self.is_jumping():
            if self.is_facing_left():
                return self.big_frames[0].tile()
            else:
                return self.big_frames[0x08].tile()
        elif self.is_flying():
            return self.get_plane_animation()[0].tile()
        elif self.is_turning():
            if self.is_facing_left():
                return self.big_frames[0x14 - self.frame_no].tile()
            else:
                return self.big_frames[0x11 + self.frame_no].tile()
        elif self.is_transforming():
            return self.small_frames[0].tile()
        else:
            if self.left_facing:
                return self.get_left_animation()[self.frame_no].tile()
            else:
                return self.get_right_animation()[self.frame_no].tile()

    def step(self):
        if not self.is_flying():
            if self.is_turning():
                self.frame_no += 1
                if self.frame_no >= 3: # This is due to an unfortunate off-by-one error that I'm adding in in terms of
                                       # timing. I don't like it, but I don't know how to fix it.
                    self.frame_no = 0 # Not quite right...
                    self.turning = False
            else:
                self.frame_no += 1
                if self.frame_no >= 8:
                    self.frame_no = 0

# Actions
    def transform(self):
        self.jumping = 0
        self.flying = not self.flying
        if self.flying:
            self.grounded = False

    def set_jumping(self, status):
        self.jumping = status

    def jump(self):
        global JUMP_MAX_HEIGHT, THX_JUMPING
        self.state = THX_JUMPING
        self.jumping += 1
        if self.jumping > JUMP_MAX_HEIGHT:
            self.jumping = 0
        return self.jumping

    def turn(self):
        self.frame_no = 0
        self.left_facing = not self.left_facing
        self.turning = True

    def fall(self):
        self.frame_no = 0
        self.state = THX_FALLING

    def land(self):
        self.state = THX_GROUNDED
        self.jumping = 0

    def set_state(self, state):
        if state == THX_FALLING:
            pass
        self.state = state

# Queries:
    def get_state(self):
        return self.state
        
    def is_turning(self):
        return self.turning

    def is_flying(self):
        return self.flying

    def is_facing_left(self):
        return self.left_facing

    def is_grounded(self):
        global THX_GROUNDED
        return self.get_state() == THX_GROUNDED

    def is_transforming(self):
        return self.transforming

    def is_jumping(self):
        global THX_JUMPING
        return self.get_state() == THX_JUMPING


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
