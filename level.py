import json

import constants
import components
import generators


from map_common import get_free_tiles, random_free_tile, random_free_tile_away, random_tile_with_desc, \
    print_map_string
from tile_lookups import TileTypes, get_index
import item_uses

from map.bspmap import BspMapGenerator
from map.bspcity import BspCityGenerator
from map.cavemap import CaveGenerator
from map.mainmap import MainMapGenerator


class obj_Level(object):
    def __init__(self, gen_type="dungeon", seed=10, starting_stairs=True):
        print("Level seed: " + str(seed))
        self.current_entities = []
        self.current_effects = []

        # level gen
        self.gen_type = gen_type
        # map gen
        if gen_type == "dungeon":
            map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                  False, seed, constants.DEBUG_MAP)
        elif gen_type == "encampment":
            #map_gen = BspCityGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE+2, 2,
            map_gen = BspCityGenerator(15, 11, constants.ROOM_MIN_SIZE+2, 2,
                                False, seed, False, constants.DEBUG_MAP)
        elif gen_type == "city":
            map_gen = BspCityGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE+2, 2,
                                False, seed, True, constants.DEBUG_MAP)
        elif gen_type == "cavern":
            map_gen = CaveGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, seed, constants.DEBUG_MAP)
        elif gen_type == "main":
            map_gen = MainMapGenerator(40, 40, 2)
        # fallback
        else:
            map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                      constants.FULL_ROOMS, seed, constants.DEBUG_MAP)
        if gen_type == "main":
            gen_map = map_gen.generate_map(False)
        else:
            gen_map = map_gen.generate_map()

        # catch degenerate instances
        if gen_type == "cavern":
            max_tiles = constants.MAP_WIDTH * constants.MAP_WIDTH
            while len(get_free_tiles(gen_map[0])) < max_tiles / 8:  # 50:
                print("Free tiles check failed, regenerating...")
                gen_map = map_gen.generate_map()

        # step 2 of main map
        if gen_type == "main":
            w, h, x, y = map_gen.test_rectangle_detection()

            # generate inner map
            inner_map_gen = BspCityGenerator(w, h, constants.ROOM_MIN_SIZE + 2, 2, False, 2, False)
            gen_inner_map = inner_map_gen.generate_map()
            inner_map, map_desc = gen_inner_map[0], gen_inner_map[1]
            print_map_string(inner_map)

            # insert inner map
            for i in range(len(inner_map)):
                for j in range(len(inner_map[0])):
                    gen_map[0][x + i][y + j] = inner_map[i][j]
                    gen_map[1][x + i][y + j] = map_desc[i][j]

        if len(gen_map) > 1:
            self.current_map, self.map_desc = gen_map[0], gen_map[1]
        else:
            self.current_map, self.map_desc = gen_map[0], [[ 0 for _ in range(len(gen_map[0][0]))] for _ in range(len(gen_map[0]))]
        if len(gen_map) > 2:
            self.player_start_x, self.player_start_y = gen_map[2], gen_map[3]
        else:
            self.player_start_x, self.player_start_y = random_free_tile(self.current_map)
        if len(gen_map) > 4:
            self.rooms = gen_map[4]

        # new way of storing explored info
        self.current_explored = [[False for _ in range(0, len(self.current_map[0]))] for _ in range(0, len(self.current_map))]

        # place stairs
        if starting_stairs:
            self.current_map[self.player_start_x][self.player_start_y] = get_index(TileTypes.STAIRS_UP)

        # debug
        print_map_string(self.current_map)



    def add_entity(self, entity):
        if entity is not None:
            self.current_entities.append(entity)

    def spawn_random_monster(self):
        self.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(self.current_map)))

    def spawn_random_monster_dist(self, dist):
        self.add_entity(generators.generate_monster(generators.generate_random_mon(),
                                *random_free_tile_away(self.current_map, dist, (self.player_start_x, self.player_start_y))))

    def spawn_item_by_id(self, i_id):
        item = generators.generate_item(i_id, *random_free_tile(self.current_map))
        self.add_entity(item)
        if item:
            item.send_to_back()
        # in case we need it later
        return item

    def spawn_monster_by_id(self, m_id):
        generators.generate_monster(m_id, *random_free_tile(self.current_map))

    def spawn_usable_item(self, tile, name, use_func):
        x, y = random_free_tile(self.current_map)
        item_com = components.com_Item(use_function=use_func)
        item = components.obj_Actor(x,y, tile, name, item=item_com)
        self.current_entities.append(item)
        item.send_to_back()

    def generate_items_monsters(self, num=0, dists=None):
        # default
        if dists is None:
            dists = []

        # test potion
        self.spawn_usable_item(0x2762, "potion", item_uses.cast_heal)

        # test potion 2
        self.spawn_usable_item(0x2762, "potion 2", item_uses.cast_strength)

        # food/drink
        self.spawn_usable_item(0x1F35E, "rations", item_uses.eat_food)
        self.spawn_usable_item(0x2615, "water flask", item_uses.drink)


        # test generating items
        self.spawn_item_by_id("longsword")
        self.spawn_item_by_id("dagger")
        self.spawn_item_by_id("studded armor")
        self.spawn_item_by_id("chainmail")

        self.add_entity(generators.generate_monster("human", *random_free_tile(self.current_map)))

        for _ in range(num):
            self.spawn_random_monster()

        for d in dists:
            self.spawn_random_monster_dist(d)

        if self.gen_type == "encampment" or self.gen_type == "city":
             # test spawning on tiles with desc
             self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))
             self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))
             self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))

        else:
             # test: force spawn a monster on top of the player
             self.add_entity(generators.generate_monster("goblin", self.player_start_x, self.player_start_y))


def load_level_data(l_id):
    if not l_id in levels_data:
        print("Wanted bad level: " + str(l_id))
        return

    # values
    gen_type = levels_data[l_id]['type']
    if 'random_spawn_num' in levels_data[l_id]:
        rnd_spawns = levels_data[l_id]['random_spawn_num']
    else:
        rnd_spawns = 0
    if 'random_spawn_dist' in levels_data[l_id]:
        rnd_spawn_dist = levels_data[l_id]['random_spawn_dist']
    else:
        rnd_spawn_dist = []

    return [gen_type, rnd_spawns, rnd_spawn_dist]


# Execute
# Load JSON
with open("data/levels-test.json") as json_data:
    levels_data = json.load(json_data)
    generators.logger.debug(levels_data)

if __name__ == '__main__':
    with open("data/levels-test.json") as json_data:
        levels_data = json.load(json_data)
        generators.logger.debug(levels_data)

    print(load_level_data("cave"))
    print(load_level_data("encampment"))