# coding: utf8

import libtcodpy as libtcod
import sys
import math
from operator import itemgetter

import constants

class struc_Tile(object):
    def __init__(self, name, tile_put, map_str, block_path):
        self.block_path = block_path
        self.name = name
        self.map_str = map_str
        self.tile_put = tile_put


tile_types = [
    struc_Tile("wall", "#", "#", True), #this is the simple wall, horizontal
    struc_Tile("wall", 0x2503, "#", True), #vertical wall
    struc_Tile("floor", 0x3002, ".", False),
    struc_Tile("sand floor", 0x3003, ".", False),
    struc_Tile("stairs", ">", ">", False)
]


room_desc = [
    "",
    "This is a room.",
    "This is an interior of a hut.",
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

def random_free_tile_away(inc_map, dist, away_from):
    away_tiles = []
    for tile in get_free_tiles(inc_map):
        if tiles_distance_to(away_from, tile) > dist:
            away_tiles.append(tile)

    index = libtcod.random_get_int(0,0, len(away_tiles)-1)
    x = away_tiles[index][0]
    y = away_tiles[index][1]
    print("[Free tile away] Coordinates are " + str(x) + " " + str(y))
    return x, y


def tiles_distance_to(start, target):
    x_diff = start[0] - target[0]
    y_diff = start[1] - target[1]
    ##ensure always positive values
    if x_diff < 0:
        x_diff = x_diff * -1
    if y_diff < 0:
        y_diff = y_diff * -1
    return max(x_diff, y_diff)


def distance_to(start, other):
    # return the distance to another object
    dx = other[0] - start[0]
    dy = other[1] - start[1]
    return math.sqrt(dx ** 2 + dy ** 2)

def find_grid_in_range(dist, x, y):
    print("Looking for grids in range " + str(dist) + " of " + str(x) + " " + str(y))
    coord_in_range = []
    for i in range(x-dist,x+dist+1):
        for j in range(y-dist, y+dist+1):
            if i > 0 and i < constants.MAP_WIDTH and j > 0 and j < constants.MAP_HEIGHT:
                distance = distance_to((x,y), (i,j))
                coord_in_range.append((i, j, distance))

    # sort 'em
    coord_in_range = sorted(coord_in_range, key=itemgetter(2))

    return coord_in_range

def find_free_grid_in_range(dist, x, y, game):
    coords = find_grid_in_range(dist, x,y)
    free = get_free_tiles(game.level.current_map)
    out = []

    for c in coords:
        if (c[0], c[1]) in free:
            if map_check_for_creature(c[0],c[1],game) is None:
                out.append((c[0], c[1]))

    return out

# admittedly not ideal here due to the reliance on game... but /shrug
def map_check_for_item(x,y, game):
    target = None

    for ent in game.level.current_entities:
        if (ent.x == x
            and ent.y == y
            and ent.item):
            target = ent

        if target:
            return target

def map_check_for_creature(x, y, game, exclude_entity = None):
    #print("Checking for creatures at " + str(x) + " " + str(y))
    target = None

    # find entity that isn't excluded
    if exclude_entity:
        for ent in game.level.current_entities:
            if (ent is not exclude_entity
                and ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

            if target:
                return target

    # find any entity if no exclusions
    else:
        for ent in game.level.current_entities:
            if (ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

            if target:
                return target


def print_map_string(inc_map):
    for y in range(len(inc_map)):
        for x in range(len(inc_map[0])):
            sys.stdout.write(tile_types[inc_map[x][y]].map_str)
        
        #our row ended, add a line break
        sys.stdout.write("\n")

def get_map_string(inc_map):
    list = []
    for y in range(len(inc_map)):
        for x in range(len(inc_map[0])):
            list.append(tile_types[inc_map[x][y]].map_str)

        # our row ended, add a line break
        list.append("\n")

    string = ''.join(list)
    #print string
    return string

def convert_to_box_drawing(inc_map):
    for y in range(len(inc_map)):
        for x in range(len(inc_map[0])):
            tile = tile_types[inc_map[x][y]]

            #print("Checking neighbors of " + str(x) + " " + str(y))

            north = y-1 > 0 and tile_types[inc_map[x][y-1]].map_str == "#"
            south = y+1 < len(inc_map) and tile_types[inc_map[x][y+1]].map_str == "#"
            west = x-1 > 0 and tile_types[inc_map[x-1][y]].map_str == "#"
            east = x+1 < len(inc_map[0]) and tile_types[inc_map[x+1][y]].map_str == "#"

            # if north:
            #     print("Wall to the north")
            # if south:
            #     print("Wall to the south")
            # if west:
            #     print("Wall to the west")
            # if east:
            #     print("Wall to the east")


            if tile.map_str == "#":
                # detect direction
                if west and east:
                    sys.stdout.write("─")
                elif north and south:
                    sys.stdout.write("│")
                # detect corners
                elif east and south:
                    sys.stdout.write("┌")
                elif west and south:
                    sys.stdout.write("┐")
                elif east and north:
                    sys.stdout.write("└")
                elif west and north:
                    sys.stdout.write("┘")

                else:
                    sys.stdout.write(tile.map_str)
            else:
                sys.stdout.write(tile.map_str)

        # our row ended, add a line break
        sys.stdout.write("\n")

def convert_walls(inc_map):
    for y in range(len(inc_map)):
        for x in range(len(inc_map[0])):
            tile = tile_types[inc_map[x][y]]

            #print("Checking neighbors of " + str(x) + " " + str(y))

            north = y-1 > 0 and tile_types[inc_map[x][y-1]].map_str == "#"
            south = y+1 < len(inc_map) and tile_types[inc_map[x][y+1]].map_str == "#"
            west = x-1 > 0 and tile_types[inc_map[x-1][y]].map_str == "#"
            east = x+1 < len(inc_map[0]) and tile_types[inc_map[x+1][y]].map_str == "#"

            if tile.map_str == "#":
                # detect direction
                if west and east:
                    inc_map[x][y] = 0
                elif north and south:
                    inc_map[x][y] = 1
                else:
                    inc_map[x][y] = 0
            else:
                inc_map[x][y] = inc_map[x][y]

    return inc_map

def print_converted(inc_map):
    new_map = convert_walls(inc_map)
    for y in range(len(new_map)):
        for x in range (len(new_map[0])):
            sys.stdout.write(tile_types[inc_map[x][y]].map_str)

        # our row ended, add a line break
        sys.stdout.write("\n")

def get_map_desc(x,y, fov_map, explored_map, desc_map=None):
    # catch if we don't have descriptions at all
    if desc_map is None:
        print("No descriptions")
        return

    is_visible = libtcod.map_is_in_fov(fov_map, x, y)

    #print("Getting map desc for " + str(x) + " " + str(y))
    #print("Desc map is " + str(desc_map[x][y]))

    if is_visible:
        if x >= 0 and x < constants.MAP_WIDTH: #len(desc_map):
            if y >= 0 and y < constants.MAP_HEIGHT: #len(desc_map[0):
                return room_desc[desc_map[x][y]]
            else:
                return ""
        else:
            return ""
    else:
        if x >= 0 and x < constants.MAP_WIDTH: #len(desc_map):
            if y >= 0 and y < constants.MAP_HEIGHT: #len(desc_map[0):
                if explored_map[x][y]:
                    return room_desc[desc_map[x][y]]
                else:
                    return ""
            else:
                return ""
