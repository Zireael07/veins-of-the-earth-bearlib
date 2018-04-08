import libtcodpy as libtcod
import random

import constants
from map_common import Rect, print_map_string, room_desc, convert_walls, debug_pause
from tile_lookups import TileTypes, get_index

class BspCityGenerator(object):
    def __init__(self, map_width, map_height, min_room_size, generation_depth, full_rooms, seed,
                 wall=False, debug=False):
        self.map_width = map_width
        self.map_height = map_height
        self.min_room_size = min_room_size
        self.generation_depth = generation_depth
        self.full_rooms = full_rooms
        self.wall = wall
        self._map = []
        self.debug = debug
        self.seed = seed

        # seed
        self.rnd = libtcod.random_new_from_seed(self.seed)

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
                    self._map[x][y] = get_index(TileTypes.WALL) #0
            #Make floors
            for x in range(minx+1, maxx):
                for y in range(miny+1, maxy):
                    self._map[x][y] = get_index(TileTypes.FLOOR) #2

            self._rooms_centers.append(((minx + maxx) // 2, (miny + maxy) // 2))

            new_room = Rect(minx, miny, node.w, node.h)
            self._rooms.append(new_room)

        return True

    def create_doors(self):
        for room in self._rooms:
            (x, y) = room.center()
            #print("Creating door for " + str(x) + " " + str(y))

            choices = ["north", "south", "east", "west"]
            # copy the list so that we don't modify it while iterating (caused some directions to be missed)
            sel_choices = list(choices)

            # check if the door leads anywhere
            for choice in choices:
                #print(str(choice)+"...")
                if choice == "north":
                    checkX = x
                    checkY = room.y1-1
                if choice == "south":
                    checkX = x
                    checkY = room.y2
                if choice == "east":
                    checkX = room.x2
                    checkY = y
                if choice == "west":
                    checkX = room.x1-1
                    checkY = y

                # if it leads to a wall, remove it from list of choices
                #print("Checking dir " + str(choice) + ": x:" + str(checkX) + " y:" + str(checkY) + " " + str(self._map[checkX][checkY]))
                if self._map[checkX][checkY] == get_index(TileTypes.WALL): #0:
                    #print("Removing direction from list" + str(choice))
                    sel_choices.remove(choice)

            #print("Choices: " + str(choices))

            wall = random.choice(sel_choices)


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

            self._map[wallX][wallY] = get_index(TileTypes.FLOOR) #2

    def create_walls(self):
        # walls around the map
        for x in range(self.map_width):
            self._map[x][0] = get_index(TileTypes.WALL) #0  # .block_path = True
            self._map[x][self.map_height - 1] = get_index(TileTypes.WALL) #0  # .block_path = True

        for y in range(self.map_height):
            self._map[0][y] = get_index(TileTypes.WALL) #0  # .block_path = True
            self._map[self.map_width - 1][y] = get_index(TileTypes.WALL) #0  # .block_path = True

    def place_decor(self):
        for room in self._rooms:
            (x, y) = room.center()
            choices = ["north", "south", "east", "west"]
            side = random.choice(choices)

            if side == "north":
                selX = x +libtcod.random_get_int(0,-1,1)
                selY = room.y1+1
            elif side == "south":
                selX = x +libtcod.random_get_int(0,-1,1)
                selY = room.y2-2
            elif side == "east":
                selX = room.x2-2
                selY = y +libtcod.random_get_int(0,-1,1)
            elif side == "west":
                selX = room.x1+1
                selY = y +libtcod.random_get_int(0,-1,1)

            self._map[selX][selY] = get_index(TileTypes.CRATE)


    def generate_build_desc(self):
        for room in self._rooms:
            for x in range(room.x1+1, room.x2-1):
                for y in range(room.y1+1, room.y2-1):
                    self.map_desc[x][y] = 2

    def _generate_empty_map(self):
        self._map = [[get_index(TileTypes.FLOOR) for _ in range(self.map_height)] for _ in range(self.map_width)]
        return self._map


    def generate_map(self):
        print("Debug: " + str(self.debug))
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

        # city wall before doors
        if self.wall:
            self.create_walls()
        debug_pause(self)


        self.create_doors()
        debug_pause(self)


        self.map_desc = [[ 0 for _ in range(self.map_height)] for _ in range(self.map_width)]

        self.generate_build_desc()

        self.place_decor()
        debug_pause(self)

        self._map[stairs_x][stairs_y] = get_index(TileTypes.STAIRS) #4 #.stairs = True

        self._map = convert_walls(self._map)

        debug_pause(self)

        # TODO: generate monsters, items, etc.
        return [self._map, self.map_desc, self._rooms_centers[0][0], self._rooms_centers[0][1], self._rooms]

if __name__ == '__main__':

    # #test map generation
    # test_attempts = 3
    # for i in range(test_attempts):
    #     map_gen = BspCityGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE+2, 2,
    #                               False, 2, True)
    #     gen_map = map_gen.generate_map()
    #     current_map, map_desc = gen_map[0], gen_map[1]
    #     print_map_string(current_map)

    map_gen = BspCityGenerator(15, 11, constants.ROOM_MIN_SIZE+2, 2, False, 2, True)
    gen_map = map_gen.generate_map()
    current_map, map_desc = gen_map[0], gen_map[1]


    print_map_string(current_map)