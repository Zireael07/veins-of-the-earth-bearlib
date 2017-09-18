import random
from math import sqrt

import constants
from map_common import print_map_string

# based on http://www.evilscience.co.uk/a-c-algorithm-to-build-roguelike-cave-systems-part-1/
# implementation from https://github.com/AtTheMatinee/dungeon-generation
class CaveGenerator(object):

    def __init__(self, map_width, map_height):
        self._map = []
        self.caves = []

        self.map_height = map_height
        self.map_width = map_width

        self.iterations = 30000
        self.neighbors = 4  # number of neighboring walls for this cell to become a wall
        self.wall_chance = 0.50  # initial probability of a cell becoming a wall, recommended to be between .35 and .55

        self.ROOM_MIN_SIZE = 20  # size in total number of cells, not dimensions
        self.ROOM_MAX_SIZE = 500  # size in total number of cells, not dimensions

        self.smooth_edges = True
        self.smoothing = 1

    def _generate_empty_map(self):
        self._map = [[0 for _ in range(self.map_height)] for _ in range(self.map_width)]
        return self._map

    def generate_map(self):
        # Creates an empty 2D array or clears existing array
        self.caves = []

        # fill with walls
        self._generate_empty_map()

        self.random_fill()

        self.create_caves()

        self.get_caves()

        self.connect_caves()

        self.smooth()
        return self._map

    def random_fill(self):
        for y in range(1, self.map_height - 1):
            for x in range(1, self.map_width - 1):
                #print("(",x,y,") = ",self._map[x][y])
                if random.random() >= self.wall_chance:
                    self._map[x][y] = 1

    def create_caves(self):
        # ==== Create distinct caves ====
        for i in xrange(0, self.iterations):
            # Pick a random point with a buffer around the edges of the map
            tile_x = random.randint(1, self.map_width - 2)  # (2,mapWidth-3)
            tile_y = random.randint(1, self.map_height - 2)  # (2,mapHeight-3)

            # if the cell's neighboring walls > self.neighbors, make it a wall
            if self.get_adjacent_walls(tile_x, tile_y) > self.neighbors:
                self._map[tile_x][tile_y] = 0
            # or make it a floor
            elif self.get_adjacent_walls(tile_x, tile_y) < self.neighbors:
                self._map[tile_x][tile_y] = 1

        self.smooth()

    def smooth(self):
        if self.smooth_edges:
            for i in xrange(0, 5):
                # Look at each cell individually and check for smoothness
                for x in range(1, self.map_width - 1):
                    for y in range(1, self.map_height - 1):
                        if (self._map[x][y] == 0) and (self.get_adjacent_walls_simple(x, y) <= self.smoothing):
                            self._map[x][y] = 1

    def create_tunnel(self, point1, point2, current_cave):
        #print("Creating a tunnel from " + str(point1) + " to " + str(point2))
        # run a heavily weighted random Walk
        # from point1 to point1
        drunkard_x = point2[0]
        drunkard_y = point2[1]
        while (drunkard_x, drunkard_y) not in current_cave:
            # ==== Choose Direction ====
            north = 1.0
            south = 1.0
            east = 1.0
            west = 1.0

            weight = 1

            # weight the random walk against edges
            if drunkard_x < point1[0]:  # drunkard is left of point1
                east += weight
            elif drunkard_x > point1[0]:  # drunkard is right of point1
                west += weight
            if drunkard_y < point1[1]:  # drunkard is above point1
                south += weight
            elif drunkard_y > point1[1]:  # drunkard is below point1
                north += weight

            # normalize probabilities so they form a range from 0 to 1
            total = north + south + east + west
            north /= total
            south /= total
            east /= total
            west /= total

            # choose the direction
            choice = random.random()
            if 0 <= choice < north:
                dx = 0
                dy = -1
            elif north <= choice < (north + south):
                dx = 0
                dy = 1
            elif (north + south) <= choice < (north + south + east):
                dx = 1
                dy = 0
            else:
                dx = -1
                dy = 0

            # ==== Walk ====
            # check colision at edges
            if (0 < drunkard_x + dx < self.map_width - 1) and (0 < drunkard_y + dy < self.map_height - 1):
                drunkard_x += dx
                drunkard_y += dy
                if self._map[drunkard_x][drunkard_y] == 0:
                    self._map[drunkard_x][drunkard_y] = 1

    # finds the walls in four directions
    def get_adjacent_walls_simple(self, x, y):
        wall_count = 0
        # print("(",x,",",y,") = ",self._map[x][y])
        if self._map[x][y - 1] == 0:  # Check north
            wall_count += 1
        if self._map[x][y + 1] == 0:  # Check south
            wall_count += 1
        if self._map[x - 1][y] == 0:  # Check west
            wall_count += 1
        if self._map[x + 1][y] == 0:  # Check east
            wall_count += 1

        return wall_count

    # finds the walls in 8 directions
    def get_adjacent_walls(self, tile_x, tile_y):
        pass
        wall_count = 0
        for x in range(tile_x - 1, tile_x + 2):
            for y in range(tile_y - 1, tile_y + 2):
                if self._map[x][y] == 0:
                    if (x != tile_x) or (y != tile_y):  # exclude (tile_x,tile_y)
                        wall_count += 1
        return wall_count

    def get_caves(self):
        # locate all the caves within self.level and store them in self.caves
        for x in range(0, self.map_width):
            for y in range(0, self.map_height):
                if self._map[x][y] == 1:
                    self.flood_fill(x, y)

        for cave_set in self.caves:
            for tile in cave_set:
                self._map[tile[0]][tile[1]] = 1


    def flood_fill(self, x, y):
        """
        flood fill the separate regions of the level, discard
        the regions that are smaller than a minimum size, and
        create a reference for the rest.
        """
        cave = set()
        tile = (x, y)
        to_fill = set([tile])
        while to_fill:
            tile = to_fill.pop()

            if tile not in cave:
                cave.add(tile)

                self._map[tile[0]][tile[1]] = 0

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x, y - 1)
                south = (x, y + 1)
                east = (x + 1, y)
                west = (x - 1, y)

                for direction in [north, south, east, west]:

                    if self._map[direction[0]][direction[1]] == 1:
                        if direction not in to_fill and direction not in cave:
                            to_fill.add(direction)

        if len(cave) >= self.ROOM_MIN_SIZE:
            self.caves.append(cave)

    def connect_caves(self):
        # Find the closest cave to the current cave
        for current_cave in self.caves:
            for point1 in current_cave: break  # get an element from cave1
            point2 = None
            distance = None
            for next_cave in self.caves:
                if next_cave != current_cave and not self.check_connectivity(current_cave, next_cave):
                    # choose a random point from next cave
                    for next_point in next_cave: break  # get an element from cave1
                    # compare distance of point1 to old and new point2
                    new_distance = self.distance_formula(point1, next_point)
                    if (new_distance < distance) or distance is None:
                        point2 = next_point
                        distance = new_distance

            if point2:  # if all tunnels are connected, point2 == None
                self.create_tunnel(point1, point2, current_cave)

    def distance_formula(self, point1, point2):
        d = sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
        return d

    def check_connectivity(self, cave1, cave2):
        # floods cave1, then checks a point in cave2 for the flood

        connectedRegion = set()
        for start in cave1: break  # get an element from cave1

        to_fill = set([start])
        while to_fill:
            tile = to_fill.pop()

            if tile not in connectedRegion:
                connectedRegion.add(tile)

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x, y - 1)
                south = (x, y + 1)
                east = (x + 1, y)
                west = (x - 1, y)

                for direction in [north, south, east, west]:

                    if self._map[direction[0]][direction[1]] == 1:
                        if direction not in to_fill and direction not in connectedRegion:
                            to_fill.add(direction)

        for end in cave2: break  # get an element from cave2

        if end in connectedRegion:
            return True

        else:
            return False

if __name__ == '__main__':

    #test map generation
    test_attempts = 3
    for i in range(test_attempts):
        map_gen = CaveGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT)

        current_map = map_gen.generate_map()
        print("Next try:")
        print_map_string(current_map)