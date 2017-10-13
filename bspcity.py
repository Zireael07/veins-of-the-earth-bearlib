import libtcodpy as libtcod
import random

import constants
from map_common import Rect, print_map_string, room_desc, convert_walls

class BspCityGenerator(object):
    def __init__(self, map_width, map_height, min_room_size, generation_depth, full_rooms):
        self.map_width = map_width
        self.map_height = map_height
        self.min_room_size = min_room_size
        self.generation_depth = generation_depth
        self.full_rooms = full_rooms
        self._map = []

    def _traverse_node(self, node, dat):
        # Create room
        if libtcod.bsp_is_leaf(node):
            minx = node.x + 1
            maxx = node.x + node.w - 1
            miny = node.y + 1
            maxy = node.y + node.h - 1
            if maxx == self.map_width - 1:
                maxx -= 1
            if maxy == self.map_height - 1:
                maxy -= 1

            if self.full_rooms == False:
                minx = libtcod.random_get_int(None, minx, maxx - self.min_room_size + 1)
                miny = libtcod.random_get_int(None, miny, maxy - self.min_room_size + 1)
                maxx = libtcod.random_get_int(None, minx + self.min_room_size - 2, maxx)
                maxy = libtcod.random_get_int(None, miny + self.min_room_size - 2, maxy)

            node.x = minx
            node.y = miny
            node.w = maxx - minx + 1
            node.h = maxy - miny + 1

            # Make building
            # Make walls
            for x in range(minx, maxx + 1):
                for y in range(miny, maxy + 1):
                    self._map[x][y] = 0
            #Make floors
            for x in range(minx+1, maxx):
                for y in range(miny+1, maxy):
                    self._map[x][y] = 2

            self._rooms_centers.append(((minx + maxx) // 2, (miny + maxy) // 2))

            new_room = Rect(minx, miny, node.w, node.h)
            self._rooms.append(new_room)

        return True

    def create_doors(self):
        for room in self._rooms:
            (x, y) = room.center()
            #print("Creating door for " + str(x) + " " + str(y))

            wall = random.choice(["north", "south", "east", "west"])
            if wall == "north":
                wallX = x
                wallY = room.y1
            elif wall == "south":
                wallX = x
                wallY = room.y2 - 1
            elif wall == "east":
                wallX = room.x2 - 1
                wallY = y
            elif wall == "west":
                wallX = room.x1
                wallY = y

            self._map[wallX][wallY] = 2


    def generate_build_desc(self):
        for room in self._rooms:
            for x in range(room.x1+1, room.x2-1):
                for y in range(room.y1+1, room.y2-1):
                    self.map_desc[x][y] = 2

    def _generate_empty_map(self):
        self._map = [[2 for _ in range(self.map_height)] for _ in range(self.map_width)]
        return self._map

    def generate_map(self):
        self._map = self._generate_empty_map()
        self._rooms_centers = []
        self._rooms = []
        bsp = libtcod.bsp_new_with_size(0, 0, self.map_width, self.map_height)
        libtcod.bsp_split_recursive(bsp, 0, self.generation_depth, self.min_room_size + 1, self.min_room_size + 1, 1.5,
                                    1.5)
        libtcod.bsp_traverse_inverted_level_order(bsp, self._traverse_node)

        stairs_x = self._rooms_centers[len(self._rooms_centers)-1][0]
        stairs_y = self._rooms_centers[len(self._rooms_centers)-1][1]

        print("Stairs x :" + str(stairs_x) + " y: " +str(stairs_y))

        self.create_doors()

        self.map_desc = [[ 0 for _ in range(self.map_height)] for _ in range(self.map_width)]

        self.generate_build_desc()

        self._map[stairs_x][stairs_y] = 4 #.stairs = True

        self._map = convert_walls(self._map)

        # TODO: generate monsters, items, etc.
        return [self._map, self.map_desc, self._rooms_centers[0][0], self._rooms_centers[0][1], self._rooms]

if __name__ == '__main__':

    #test map generation
    test_attempts = 3
    for i in range(test_attempts):
        map_gen = BspCityGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE+1, 2,
                                  False)
        gen_map = map_gen.generate_map()
        current_map, map_desc = gen_map[0], gen_map[1]
        print_map_string(current_map)