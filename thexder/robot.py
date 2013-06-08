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


# This loops to make things work well.
THX_FLYING_ANIM = [0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,
                   0x2e,0x2f,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28]
                   
THX_WALKING_RIGHT_ANIM = [0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f]
THX_WALKING_LEFT_ANIM = [0x0,0x01,0x02,0x03,0x04,0x05,0x06,0x07]
THX_TRANSFORMING_RIGHT_ANIM = [0x16,0x17,0x1c,0x1d,0x1e,0x1f]
THX_TRANSFORMING_LEFT_ANIM = [0x14,0x15,0x18,0x19,0x1a,0x1b]
THX_TURNING_ANIM = [0x12,0x13]
THX_LANDING_LEFT_ANIM = [0x10]
THX_LANDING_RIGHT_ANIM = [0x11]

THX_DYING = [0x30, 0x31, 0x32]

THX_SAME_DIR = 0x100

#
# This just returns the animation for rotation, given an input and output direction.
#
# TODO: The only problem with this is that I think that in your first part of a turn,
#       it might start one frame late, timing-wise.
#
# This ends up being a little kludge-y, but I'm not sure as of yet a better way to address it.

def turn_animation(dir_in, dir_out):
    shift = cmp(dir_out - dir_in, 0)
    if abs(dir_in - dir_out) < 8:
        return THX_FLYING_ANIM[dir_in:dir_out:shift]
    elif abs(dir_in - dir_out) == 8:
        if dir_in < dir_out:
            return THX_FLYING_ANIM[dir_in + 0x10:dir_out: -1]
        else:
            return THX_FLYING_ANIM[dir_in:dir_out:-1]
    else:
        if dir_in < dir_out:
            return THX_FLYING_ANIM[dir_in + 0x10: dir_out:-1]
        else:
            return THX_FLYING_ANIM[dir_in:dir_out + 0x10]

class rState(object):
    def __init__(self, flags=0, direction=THX_SAME_DIR):
        self.direction = direction
        self.flags = flags

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
        big_frames_raw = content[:big_frame_bits * 0x18]
        small_frames_raw = content[big_frame_bits * 0x18:]

        # And now we make them into a bunch of tiles.
        self.big_frames = []
        for i in range(0, len(big_frames_raw) / big_frame_bits):
            self.big_frames.append(animation.Tile(big_frames_raw, 
                    i * big_frame_bits, 3 * TILE_WIDTH, 4 * TILE_HEIGHT))

        self.small_frames = []
        for i in range(0, len(small_frames_raw) / small_frame_bits):
            self.small_frames.append(animation.Tile(small_frames_raw,
                    i * small_frame_bits, 3 * TILE_WIDTH, 3 * TILE_HEIGHT))

        self.jump_height = 0

        self.enmax = 100
        self.health = 100
        self.score = 0
        
        self.tiles = self.big_frames
        self.tiles.extend(self.small_frames)
        self.step_count = 0
        self.reel = []
        self.thx_state = rState(THX_FLAG_ROBOT, DIR_E)
        
        self.shots_fired = 0
        
        self.shield_value = 0
        
        self.aiming = DIR_E

        self.frame = animation.frame(19,11,3,4) # These are the default starting parameters. It may be worth
                                                # allowing this to be mutable...
# Animations.


# Queries
    def get_ident(self):
        return THX_SPRITE
        
    def get_frame(self):
        return self.frame

    def x(self):
        return self.get_frame().x
        
    def y(self):
        return self.get_frame().y
    
    def width(self):
        return self.get_frame().width
        
    def height(self):
        return self.get_frame().height

    def direction(self):
        return self.query_state().direction
        
    def flags(self):
        return self.query_state().flags

    def is_robot(self):
        return self.flags() & THX_FLAG_ROBOT

    def is_grounded(self):
        return (self.flags() & (THX_FLAG_FALL | THX_FLAG_JUMP)) == 0
        
    def is_jumping(self):
        return self.flags() & THX_FLAG_JUMP
        
    def is_falling(self):
        return self.flags() & THX_FLAG_FALL

    def get_health(self):
        return self.health
        
    def facing(self):
        """
        This should only be called when in flight mode. It will return the actual
        direction the jet is facing.
        
        This has two uses: One of them is to keep track of animation if you rapidly
        change direction.
        
        The other use is that when eventually I implement the laser, it needs to know
        which way to fire it...
        """
        if not self.is_robot():
            if len(self.reel):
                return self.reel[0] - 0x20
        return self.direction()

    def is_dead(self):
        return self.flags() & THX_FLAG_DEAD
        
    def shield(self):
        return self.shield_value
        
# Set methods
    def change_score(self, d_score):
        self.score += d_score * 25
    
    def change_health(self, d_health):
        self.health += d_health
        if self.health > self.enmax:
            self.health = self.enmax
        
        if self.get_health() <= 0:
            self.die()
            
    def change_enmax(self, d_enmax):
        self.enmax += d_enmax
        if self.enmax > 500:
            self.enmax = 500

    def set_state(self, state):
        self.thx_state = state 
        
    def set_flags(self, flags):
        self.set_state(rState(flags, self.direction()))
    
    def set_direction(self, direction):
        self.set_state(rState(self.flags(), direction))
        
    def set_frame(self, frame):
        self.frame = frame
        
    def set_x(self, x):
        self.frame.x = x
        
    def set_y(self, y):
        self.frame.y = y

# Actions

    def take_damage(self, damage=2):
        if self.shield() >= 0:
            self.shield_value -= damage
            return False
        else:
            self.change_health(-1 * damage)
            return True

    def fire(self):
        self.shots_fired += 1
        if self.shots_fired % THX_LASER_COUNT == 0:
            self.take_damage()

    def step(self):
        self.step_count += 1
        if self.step_count >= 8:
            self.step_count = 0

    def jump(self):
        self.set_flags(THX_FLAG_JUMP | THX_FLAG_ROBOT)
        self.jump_height += 1
        if self.jump_height > JUMP_MAX_HEIGHT:
            self.push_flags(THX_FLAG_FALL | THX_FLAG_ROBOT)
            self.jump_height = 0
        return self.jump_height
        
        
    def land(self):
        self.jump_height = 0
        self.push_flags(THX_FLAG_ROBOT)
        
    def fall(self):
        self.set_flags(THX_FLAG_ROBOT | THX_FLAG_FALL)

    def transform(self):
        if self.is_robot():
            self.push_state(rState(THX_FLAG_JET))
            self.set_frame(animation.frame(self.x(), self.y(), 3, 3))
        else:
            self.push_state(rState(THX_FLAG_ROBOT))
            self.set_frame(animation.frame(self.x(), self.y(), 3, 4))

    def wait(self):
        return self.flags() & (THX_FLAG_TRANSFORMING | THX_FLAG_DEAD)
        
    def tick(self):
        if self.health > self.enmax:
            self.health = self.enmax
        if len(self.reel):
            self.reel.pop(0) # This just knocks off one frame in the animation.
        elif self.flags() & THX_FLAG_TRANSFORMING:
            self.clearflag(THX_FLAG_TRANSFORMING)
            
        if self.shield():
            self.shield_value -= 1

    def shield_on(self):
        self.shield_value = THX_SHIELD_STRENGTH
        self.change_health(-10)

    def die(self):
        self.push_flags(THX_FLAG_DEAD)

# New interface
        
    def clearflag(self, flag):
        fl = self.flags()
        if fl & flag:
            self.set_state(rState(fl - flag, self.direction()))
        
    def tile(self):
        if len(self.reel):                   # If there is a current animation...
            return self.tiles[self.reel[0]].tile() # ... use that frame.
        else:
            # Return whatever other frame we should use.
            
            if not self.is_robot(): 
                return self.tiles[THX_FLYING_FRAMES + self.direction()].tile()
            else:
                if self.is_grounded():
                    if self.direction() == DIR_E:
                        return self.tiles[0x08 + self.step_count].tile()
                    else:
                        return self.tiles[0 + self.step_count].tile()
                else:
                    if self.direction() == DIR_E:
                        return self.tiles[0x0a].tile()
                    else:
                        return self.tiles[0x00].tile()
    
     
    def push_direction(self, direction):
        flag = self.flags()
        if not self.is_robot():
        
            # TODO: This still doesn't work quite right.
            
            if DIR_N < direction < DIR_S:
                flag = THX_FLAG_JET | THX_FLAG_E_FACING_JET 
            elif direction < DIR_N or DIR_S < direction:
                flag = THX_FLAG_JET
        self.push_state(rState(flag, direction))
        
    def push_flags(self, flags):
        self.push_state(rState(flags, self.direction()))
  
    def push_state(self, state):
        """
        This is the function that maintains and switches between the internal states
        of the robot. It takes as input an rState object, which is just something which 
        encapsulates a direction and some flags.
        
        There are two auxiliary methods which simply change the state or direction.
        """
        if state.flags & THX_FLAG_DEAD:
            self.reel = THX_DYING[:]
        if state.flags & THX_FLAG_JET and self.is_robot(): # Transform to jet
            if self.direction() == DIR_E:
                self.reel = THX_TRANSFORMING_RIGHT_ANIM[:]
            else:
                self.reel = THX_TRANSFORMING_LEFT_ANIM[:]
            self.thx_state = rState(THX_FLAG_JET | THX_FLAG_TRANSFORMING, self.direction())
        elif state.flags & THX_FLAG_ROBOT and not self.is_robot(): # Transform to robot
        
            robot_direction = self.direction()
            if robot_direction == DIR_S or robot_direction == DIR_N:
                if self.flags() & THX_FLAG_E_FACING_JET:
                    self.reel = THX_TRANSFORMING_RIGHT_ANIM[::-1]
                    direction = DIR_E
                else:
                    self.reel = THX_TRANSFORMING_LEFT_ANIM[::-1]
                    direction = DIR_W
            elif DIR_N < robot_direction < DIR_S:
                self.reel = THX_TRANSFORMING_RIGHT_ANIM[::-1]
                direction = DIR_E
            else:
                self.reel = THX_TRANSFORMING_LEFT_ANIM[::-1]
                direction = DIR_W
            self.thx_state = rState(THX_FLAG_ROBOT | THX_FLAG_TRANSFORMING, direction)

        elif self.is_robot():
            if state.direction == DIR_E:
                if self.direction() == DIR_W:
                    self.reel = THX_TURNING_ANIM[:]
                self.set_direction(DIR_E)
            elif state.direction == DIR_W:
                if self.direction() == DIR_E:
                    self.reel = THX_TURNING_ANIM[::-1]
                self.set_direction(DIR_W)
            
            if (self.flags() & THX_FLAG_FALL or self.flags() & THX_FLAG_JUMP) and state.flags == THX_FLAG_ROBOT:
                if self.direction() == DIR_E:
                    self.reel = THX_LANDING_RIGHT_ANIM[:]
                else:
                    self.reel = THX_LANDING_LEFT_ANIM[:]
                self.set_flags(THX_FLAG_ROBOT)
        else:
            # We are a plane, and are trying to change direction.
            if state.direction != self.facing():
            
                self.reel = turn_animation(self.facing(), state.direction)
                self.set_flags(state.flags)
                self.set_direction(state.direction)

        
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
