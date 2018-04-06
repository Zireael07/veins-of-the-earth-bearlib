import libtcodpy as libtcod

from map_common import print_map_string, Directions
from tile_lookups import TileTypes, get_index

class NoiseMapGenerator(object):
    def __init__(self, map_width, map_height, seed, lacunarity=2.0, hurst=0.5, noise_zoom=1, noise_octaves=10, debug=False):
        self.map_width = map_width
        self.map_height = map_height
        self.noise_zoom = noise_zoom
        self.noise_octaves = noise_octaves
        self.lacunarity = lacunarity
        self.hurst = hurst
        self._map = []
        self.debug = debug
        self.seed = seed

        # seed
        self.rnd = libtcod.random_new_from_seed(self.seed)

    def generate_heightmap_values(self, hm):
        hvs = [[0 for _ in range(self.map_height)] for _ in range(self.map_width)]
        for x in range(self.map_width):
            for y in range(self.map_height):
                hm_v = libtcod.heightmap_get_value(hm, x, y)
                # multiply by 100
                hv = int(hm_v * 100)
                hvs[x][y] = hv

        return hvs

    def _generate_empty_map(self):
        self._map = [[get_index(TileTypes.WALL) for _ in range(self.map_height)] for _ in range(self.map_width)]
        return self._map

    def generate_map_from_heightmap(self):
        for x in range(self.map_width):
            for y in range(self.map_height):
                # we want more floor than rock
                if self.heightmap[x][y] > 60:
                    self._map[x][y] = get_index(TileTypes.WALL)
                else:
                    self._map[x][y] = get_index(TileTypes.FLOOR)

    def generate_heightmap(self):
        print("Hurst: " + str(self.hurst) + " lacuna: " + str(self.lacunarity))

        hm = libtcod.heightmap_new(self.map_width, self.map_height)
        hm1 = libtcod.heightmap_new(self.map_width, self.map_height)
        hm2 = libtcod.heightmap_new(self.map_width, self.map_height)

        noise = libtcod.noise_new(2, self.hurst, self.lacunarity, self.rnd)
        #print(str(noise))

        libtcod.heightmap_add_fbm(hm1, noise, self.noise_zoom, self.noise_zoom, 0.0, 0.0, self.noise_octaves, 0.0, 1.0)
        #libtcod.heightmap_add_fbm(hm, noise, 1.5, 1.5, 1.2, 1.2, self.noise_octaves, 0.5, 0.5)

        libtcod.heightmap_add_fbm(hm2, noise, self.noise_zoom * 2, self.noise_zoom * 2, 0.0, 0.0, self.noise_octaves / 2, 0.0, 1.0)

        #libtcod.heightmap_add_hm(hm1, hm2, hm)

        libtcod.heightmap_multiply_hm(hm1, hm2, hm)
        libtcod.heightmap_normalize(hm, mi=0.0, ma=1)

        # use the heightmap
        heightmap = self.generate_heightmap_values(hm)
        print(heightmap)


        # clean up once not needed
        libtcod.heightmap_delete(hm)
        libtcod.heightmap_delete(hm1)
        libtcod.heightmap_delete(hm2)

        return heightmap

    def generate_map(self):
        print("Mapgen seed: " + str(self.seed))

        self._map = self._generate_empty_map()
        #print(str(self._map))

        self.heightmap = self.generate_heightmap()

        self.generate_map_from_heightmap()

        return self._map

    def get_space_flood(self):
        for x in range(0, self.map_width):
            for y in range(0, self.map_height):
                if self._map[x][y] == get_index(TileTypes.FLOOR): #2:
                    # we start from top left
                    print("Starting flood from x,y " + str(x) + "," + str(y))
                    self.flood_fill(x, y)


    def flood_fill(self, x, y):
        """
        flood fill the separate regions of the level
        """
        cave = set()
        tile = (x, y)
        to_fill = set([tile])
        while to_fill:
            tile = to_fill.pop()

            if tile not in cave:
                cave.add(tile)

                self._map[tile[0]][tile[1]] = get_index(TileTypes.CRATE) #0

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x+Directions.NORTH[0], y + Directions.NORTH[1])
                south = (x+Directions.SOUTH[0], y + Directions.SOUTH[1])
                east = (x + Directions.EAST[0], y + Directions.EAST[1])
                west = (x + Directions.WEST[0], y + Directions.WEST[1])

                for direction in [north, south, east, west]:

                    if self._map[direction[0]][direction[1]] == get_index(TileTypes.FLOOR): #2:
                        if direction not in to_fill and direction not in cave:
                            to_fill.add(direction)

    # 'scanline fill', being done line by line
    def get_space_line(self):
        for x in range(0, self.map_width):
            for y in range(0, self.map_height):
                if self._map[x][y] == get_index(TileTypes.FLOOR): #2:
                    # we start from top left
                    #print("Starting line fill from x,y " + str(x) + "," + str(y))
                    self.line_fill(x, y)

    # Simply expand east until we encounter a wall or end of map
    def line_fill(self, x,y):
        #initial_tile = (x,y)
        cave = set()
        tile = (x, y)
        to_fill = set([tile])
        while to_fill:
            tile = to_fill.pop()

            if tile not in cave:
                cave.add(tile)

                # to debug
                self._map[tile[0]][tile[1]] = get_index(TileTypes.CRATE)  # 0

                # check adjacent cells
                x = tile[0]
                y = tile[1]

                east = (x + Directions.EAST[0], y + Directions.EAST[1])

                if east[0] >= len(self._map[0]):
                    #print("East is out of map, breaking loop")
                    break

                if self._map[east[0]][east[1]] == get_index(TileTypes.FLOOR): #2:
                    if east not in to_fill and east not in cave:
                        to_fill.add(east)


if __name__ == '__main__':

    #test map generation

    # default
    map_gen = NoiseMapGenerator(40, 40, 2)
    current_map = map_gen.generate_map()

    print_map_string(current_map)

    # # test single line fill
    # print("Linefill")
    # map_gen.line_fill(0,0)
    # print_map_string(current_map)

    print("Test space line")
    map_gen.get_space_line()

    #print("After floodfill")
    #map_gen.get_space_flood()

    print_map_string(current_map)

    # changing hurst doesn't seem to do anything at least for 40x40

    # map_gen = NoiseMapGenerator(40, 40, 2, 1.5)
    # current_map = map_gen.generate_map()
    # print_map_string(current_map)
    #
    # map_gen = NoiseMapGenerator(40, 40, 2, 1.0)
    # current_map = map_gen.generate_map()
    # print_map_string(current_map)
    #
    # map_gen = NoiseMapGenerator(40, 40, 2, 3.0)
    # current_map = map_gen.generate_map()
    # print_map_string(current_map)