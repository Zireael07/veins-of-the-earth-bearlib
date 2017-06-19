from bearlibterminal import terminal as blt
import libtcodpy as libtcod

MAP_HEIGHT = 20
MAP_WIDTH = 20

# in number of cells
TILE_HEIGHT = 2
TILE_WIDTH = 4

#FOV
FOV_ALGO = libtcod.FOV_BASIC
FOV_LIGHT_WALLS = True
LIGHT_RADIUS = 4


# Tiles
blt.set("0x02E: gfx/floor_sand.png")
blt.set("0x23: gfx/wall_stone.png")