from bearlibterminal import terminal as blt
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


#FOV
FOV_ALGO = libtcod.FOV_BASIC
FOV_LIGHT_WALLS = True
LIGHT_RADIUS = 4

NUM_MESSAGES = 4

DEBUG = False

# Data
NPC_JSON_PATH = "data/test.json"
ITEMS_JSON_PATH = "data/items.json"

# Debug map
DEBUG_MAP = True
STARTING_MAP = "city"