import libtcodpy as libtcod

MAP_HEIGHT = 20
MAP_WIDTH = 20

#BSP settings
DEPTH = 3
ROOM_MIN_SIZE = 4
FULL_ROOMS = True

# in number of cells
TILE_HEIGHT = 2
TILE_WIDTH = 8

HALF_TILE_HEIGHT = 1
HALF_TILE_WIDTH = 4
CAMERA_OFFSET = 80

# cache the isometric calculations instead of doing them every frame
# this wouldn't be necessary for a non-iso game since the calculations would be almost nonexistent
# moved to constants since it only needs some constants to work
def iso_pos(x,y):
    # isometric
    offset_x = CAMERA_OFFSET
    #hw = HALF_TILE_WIDTH
    #hh = HALF_TILE_HEIGHT
    tile_x = (x - y) * HALF_TILE_WIDTH + offset_x
    tile_y = (x + y) * HALF_TILE_HEIGHT
    return tile_x, tile_y

# some maximum size
RENDER_POSITIONS = [[iso_pos(x, y) for y in range(0, 70)] for x in range(0, 70)]



#FOV (used by both player and AI)
# 'basic' is called circular raycasting in source
FOV_ALGO = libtcod.FOV_BASIC
#FOV_ALGO = libtcod.FOV_DIAMOND
# libtcod's shadowcasting gives circular fov, not square
#FOV_ALGO = libtcod.FOV_SHADOW
# this is the only one that gives equal radius in all directions (square and not circular)
#FOV_ALGO = libtcod.FOV_PERMISSIVE_6
FOV_LIGHT_WALLS = True
#LIGHT_RADIUS = 4

NUM_MESSAGES = 4

DEBUG = False

# Data
NPC_JSON_PATH = "data/test.json"
ITEMS_JSON_PATH = "data/items.json"

# Debug map
DEBUG_MAP = True
STARTING_MAP = "main"