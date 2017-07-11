import libtcodpy as libtcod

import constants

class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False

def map_make_fov(incoming_map):
    #global FOV_MAP

    #FOV_MAP = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)
    fov_map = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    for y in range(constants.MAP_HEIGHT):
        for x in range(constants.MAP_WIDTH):
            #libtcod.map_set_properties(FOV_MAP, x,y,
            libtcod.map_set_properties(fov_map, x,y,
                                       not incoming_map[x][y].block_path, not incoming_map[x][y].block_path)

    return fov_map