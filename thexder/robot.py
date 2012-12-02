from constants import *
import animation

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

    def __init__(self, filename="ROBOT.BIN"):   
        global TILE_WIDTH, TILE_HEIGHT
        content = data.default_data_manager().load_file(filename)

        # The number of bits per frame.
        big_frame_bits = 3 * 4 * TILE_HEIGHT * TILE_WIDTH /2
        small_frame_bits = 3 * 3 * TILE_HEIGHT * TILE_WIDTH /2

        # This separates it into the large and small frames, which will be processed separately.
        big_frames = content[:big_frame_bits * 0x18]
        small_frames = content[big_frame_bits * 0x18:]

        self.animation_left = None
        self.animation_right = None
        self.animation_plane = None
        self.animation_turning = None
        self.animation_landing_left = None
        self.animation_landing_right = None
        self.animation_transform_right = None
        self.animation_transform_left = None

