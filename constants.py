from bearlibterminal import terminal as blt
import libtcodpy as libtcod

MAP_HEIGHT = 20
MAP_WIDTH = 20

#BSP settings
DEPTH = 5
ROOM_MIN_SIZE = 4
FULL_ROOMS = False

# in number of cells
TILE_HEIGHT = 2
TILE_WIDTH = 8

#FOV
FOV_ALGO = libtcod.FOV_BASIC
FOV_LIGHT_WALLS = True
LIGHT_RADIUS = 4

NUM_MESSAGES = 4


# Tiles
blt.set("0x02E: gfx/floor_sand.png")
blt.set("0x23: gfx/wall_stone.png")

# Data
NPC_JSON_PATH = "data/test.json"
ITEMS_JSON_PATH = "data/items.json"