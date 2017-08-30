import libtcodpy as libtcod
import sys

import constants

class struc_Tile(object):
    def __init__(self, name, tile_put, map_str, block_path):
        self.block_path = block_path
        self.name = name
        self.map_str = map_str
        self.tile_put = tile_put


tile_types = [
    struc_Tile("wall", "#", "#", True),
    struc_Tile("floor", 0x3002, ".", False),
    struc_Tile("sand floor", 0x3003, ".", False),
    struc_Tile("stairs", ">", ">", False)
]


class Rect(object):
    """
    A rectangle on the map. used to characterize a room.
    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + max(0, w)
        self.y2 = y + max(0, h)

    def __eq__(self, other):
        return (self.x1 == other.x1 and
                self.x2 == other.x2 and
                self.y1 == other.y1 and
                self.y2 == other.y2)

    def center(self):
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    def intersect(self, other):
        """
        Returns true if two rectangles intersect.
        """
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

    def contains(self, location):
        return (location[0] >= self.x1 and location[0] <= self.x2 and
                self.y1 <= location[1] <= self.y2)

    def update(self, x,y,w,h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + max(0,w)
        self.y2 = y + max(0,h)

def map_make_fov(incoming_map):
    #global FOV_MAP

    #FOV_MAP = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)
    fov_map = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    for y in range(constants.MAP_HEIGHT):
        for x in range(constants.MAP_WIDTH):
            #libtcod.map_set_properties(FOV_MAP, x,y,
            libtcod.map_set_properties(fov_map, x,y,
                                      # not incoming_map[x][y].block_path, not incoming_map[x][y].block_path)
                                        not tile_types[incoming_map[x][y]].block_path,
                                       not tile_types[incoming_map[x][y]].block_path)

    return fov_map

def get_free_tiles(inc_map):
    free_tiles = []
    for y in range(len(inc_map)):
        for x in range(len(inc_map[0])):
            if not tile_types[inc_map[x][y]].block_path:
                free_tiles.append((x,y))
    return free_tiles

def random_free_tile(inc_map):
    free_tiles = get_free_tiles(inc_map)
    index = libtcod.random_get_int(0, 0, len(free_tiles)-1)
    #print("Index is " + str(index))
    x = free_tiles[index][0]
    y = free_tiles[index][1]
    print("Coordinates are " + str(x) + " " + str(y))
    return x, y

# admittedly not ideal here due to the reliance on game... but /shrug
def map_check_for_item(x,y, game):
    target = None

    for ent in game.current_entities:
        if (ent.x == x
            and ent.y == y
            and ent.item):
            target = ent

        if target:
            return target

def print_map_string(inc_map):
    for y in range(len(inc_map)):
        for x in range(len(inc_map[0])):
            sys.stdout.write(tile_types[inc_map[x][y]].map_str)
        
        #our row ended, add a line break
        sys.stdout.write("\n")
