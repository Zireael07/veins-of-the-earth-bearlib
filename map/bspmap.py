import libtcodpy as libtcod

import constants
from map_common import Rect, print_map_string, convert_to_box_drawing, convert_walls, print_converted, debug_pause
from tile_lookups import TileTypes, get_index

class BspMapGenerator(object):
    def __init__(self, map_width, map_height, min_room_size, generation_depth, full_rooms, seed, debug=False):
        self.map_width = map_width
        self.map_height = map_height
        self.min_room_size = min_room_size
        self.generation_depth = generation_depth
        self.full_rooms = full_rooms
        self._map = []
        self.debug = debug
        self.seed = seed

        # seed
        self.rnd = libtcod.random_new_from_seed(self.seed)

    def _vline(self, x, y1, y2):
        print("Generating a corridor from " + str(x) + " " + str(y1) + " to " + str(x) + " " + str(y2))
        if y1 > y2:
            y1, y2 = y2, y1
        for y in range(y1, y2 + 1):
            self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False

    def _vline_up(self, x, y):
        print("Generating a corridor from " + str(x) + " " + str(y) + " upwards")
        if x > self.map_width -1:
            return

        while y > 0 and self._map[x][y] == get_index(TileTypes.WALL): #0: #.block_path == True:
            self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False
            y -= 1

    def _vline_down(self, x, y):
        print("Generating a corridor from " + str(x) + " " + str(y) + " downwards")
        if x > self.map_width -1:
            return

        while y < self.map_height - 1 and self._map[x][y] == get_index(TileTypes.WALL): #0: # .block_path == True:
            self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False
            y += 1

    def _hline(self, x1, y, x2):
        print("Generating a corridor from " + str(x1) + " " + str(y) + " to " + str(x2) + " " + str(y))
        if x1 > x2:
            x1, x2 = x2, x1
        for x in range(x1, x2 + 1):
            self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False

    def _hline_left(self, x, y):
        print("Generating a corridor from " + str(x) + " " + str(y) + " left")
        if y > self.map_height - 1:
            return

        while x > 0 and self._map[x][y] == get_index(TileTypes.WALL): #0: #.block_path == True:
            self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False
            x -= 1

    def _hline_right(self, x, y):
        print("Generating a corridor from " + str(x) + "  " + str(y) + " right")
        if y > self.map_height - 1:
            return
        while x < self.map_width - 1 and self._map[x][y] == get_index(TileTypes.WALL): #0: #.block_path == True:
            self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False
            x += 1

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

            # Dig room
            for x in range(minx, maxx + 1):
                for y in range(miny, maxy + 1):
                    self._map[x][y] = get_index(TileTypes.FLOOR) #2 #.block_path = False
            self._rooms_centers.append(((minx + maxx) // 2, (miny + maxy) // 2))

            new_room = Rect(minx, miny, node.w, node.h)
            self._rooms.append(new_room)

            # pause after every room
            debug_pause(self)

        # Create corridor
        else:
            left = libtcod.bsp_left(node)
            right = libtcod.bsp_right(node)
            node.x = min(left.x, right.x)
            node.y = min(left.y, right.y)
            node.w = max(left.x + left.w, right.x + right.w)
            node.h = max(left.y + left.h, right.y + right.h)
            if node.horizontal:
                if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:
                    x1 = libtcod.random_get_int(None, left.x, left.x + left.w - 1)
                    x2 = libtcod.random_get_int(None, right.x, right.x + right.w - 1)
                    y = libtcod.random_get_int(None, left.y + left.h, right.y)
                    print("Generating corridors horizontal case 1 for " + str(x1) + " " + str(y) + ", " + str(x2) + " " + str(y))
                    self._vline_up(x1, y - 1)
                    self._hline(x1, y, x2)
                    self._vline_down(x2, y + 1)

                    debug_pause(self)

                else:
                    minx = max(left.x, right.x)
                    maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                    x = libtcod.random_get_int(None, minx, maxx)
                    print("Generating corridors horizontal case 2 for x " + str(x) + " y " + str(right.y) + " " + str(right.y-1))

                    # catch out-of-bounds attempts
                    while x > self.map_width - 2:
                        x -= 1

                    self._vline_down(x, right.y)
                    self._vline_up(x, right.y - 1)

                    debug_pause(self)
            else:
                if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
                    y1 = libtcod.random_get_int(None, left.y, left.y + left.h - 1)
                    y2 = libtcod.random_get_int(None, right.y, right.y + right.h - 1)
                    x = libtcod.random_get_int(None, left.x + left.w, right.x)
                    print("Generating corridors vertical case 1 for " + str(x) + " " + str(y1) + ", " + str(x) + str(y2))
                    self._hline_left(x - 1, y1)
                    self._vline(x, y1, y2)
                    self._hline_right(x + 1, y2)

                    debug_pause(self)
                else:
                    miny = max(left.y, right.y)
                    maxy = max(left.y + left.h - 1, right.y + right.h - 1)
                    y = libtcod.random_get_int(None, miny, maxy)
                    print("Generating corridors vertical case 2 for y " + str(y) + " x " + str(right.x) + " " + str(right.x-1))

                    # catch out-of-bounds attempts
                    while y > self.map_height - 2:
                        y -= 1

                    self._hline_left(right.x - 1, y)
                    self._hline_right(right.x, y)

                    debug_pause(self)
        return True

    def _generate_empty_map(self):
        self._map = [[get_index(TileTypes.WALL) for _ in range(self.map_height)] for _ in range(self.map_width)]
        return self._map

    def generate_room_desc(self):
        for room in self._rooms:
            for x in range(room.x1, room.x2):
                for y in range(room.y1, room.y2):
                    self.map_desc[x][y] = 1

    def generate_map(self):
        print("Mapgen seed: " + str(self.seed))

        self._map = self._generate_empty_map()
        debug_pause(self)
        self._rooms_centers = []
        self._rooms = []
        bsp = libtcod.bsp_new_with_size(0, 0, self.map_width, self.map_height)
        libtcod.bsp_split_recursive(bsp, self.rnd, self.generation_depth, self.min_room_size + 1, self.min_room_size + 1, 1.5,
                                    1.5)
        libtcod.bsp_traverse_inverted_level_order(bsp, self._traverse_node)
        debug_pause(self)

        stairs_x = self._rooms_centers[len(self._rooms_centers)-1][0]
        stairs_y = self._rooms_centers[len(self._rooms_centers)-1][1]

        print("Stairs x :" + str(stairs_x) + " y: " +str(stairs_y))

        self._map[stairs_x][stairs_y] = get_index(TileTypes.STAIRS)#4 #.stairs = True

        self._map = convert_walls(self._map)
        debug_pause(self)

        self.map_desc = [[0 for _ in range(self.map_height)] for _ in range(self.map_width)]

        self.generate_room_desc()

        # TODO: generate monsters, items, etc.
        return [self._map, self.map_desc, (self._rooms_centers[0][0], self._rooms_centers[0][1]), self._rooms]


if __name__ == '__main__':

    #test map generation
    test_attempts = 3
    for i in range(test_attempts):
        map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                  constants.FULL_ROOMS, 2)
        gen_map = map_gen.generate_map()
        current_map, map_desc = gen_map[0], gen_map[1]
        print_map_string(current_map)
        #convert_to_box_drawing(current_map)
        print_converted(current_map)

