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

# (type, kwargs, do we use the passed seed?, more kwargs if any)
generator_list = {
    "dungeon" : (BspMapGenerator, {"map_width":constants.MAP_WIDTH, "map_height":constants.MAP_HEIGHT,
                                   "min_room_size":constants.ROOM_MIN_SIZE, "generation_depth":constants.DEPTH,
                                  "full_rooms":False}, True, {"debug":constants.DEBUG_MAP}),
    "encampment": (BspCityGenerator, {"map_width":15, "map_height":11, "min_room_size":constants.ROOM_MIN_SIZE+2,
                                      "generation_depth":2, "full_rooms":False}, True, {"wall":False, "debug":constants.DEBUG_MAP}),
    "city": (BspCityGenerator, {"map_width":constants.MAP_WIDTH, "map_height":constants.MAP_HEIGHT,
                                "min_room_size":constants.ROOM_MIN_SIZE+2, "generation_depth":2, "full_rooms":False}, True,
             {"wall":True, "debug":constants.DEBUG_MAP}),
    "cavern": (CaveGenerator, {"map_width":constants.MAP_WIDTH, "map_height":constants.MAP_HEIGHT}, True, {"debug":constants.DEBUG_MAP}),
    "main": (MainMapGenerator, {"map_width":40, "map_height":40, "seed":2}, False, {}),
    "fallback": (BspMapGenerator, {"map_width":constants.MAP_WIDTH, "map_height":constants.MAP_HEIGHT,
                                   "min_room_size":constants.ROOM_MIN_SIZE, "generation_depth":constants.DEPTH,
                                   "full_rooms":constants.FULL_ROOMS}, True, {"debug":constants.DEBUG_MAP})
}


class obj_Level(object):
    def __init__(self, gen_type="dungeon", seed=10, starting_stairs=True):
        print("Level seed: " + str(seed))
        self.current_entities = []
        self.current_effects = []

        # level gen
        self.gen_type = gen_type
        # map gen choice
        # fallback
        if not gen_type in generator_list:
            gen_type = "fallback"

        # magic!
        params = generator_list[gen_type][1]
        params.update(generator_list[gen_type][3])
        use_seed = generator_list[gen_type][2]
        if use_seed:
            # we have to use kwargs since one can't use args and a keyword argument in 2.7
            # https://docs.python.org/2.7/reference/expressions.html point 5.3.4
            map_gen = generator_list[gen_type][0](seed=seed, **params)
        else:
            map_gen = generator_list[gen_type][0](**params)

        # specific stuff
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
            inner_map, map_desc, pl_start, poi = gen_inner_map[0], gen_inner_map[1], gen_inner_map[2], gen_inner_map[3]
            print_map_string(inner_map)

            # insert inner map
            for i in range(len(inner_map)):
                for j in range(len(inner_map[0])):
                    gen_map[0][x + i][y + j] = inner_map[i][j]
                    gen_map[1][x + i][y + j] = map_desc[i][j]

            # keep start pos and poi from inner map
            gen_map[2] = pl_start[0]+x, pl_start[1]+y
            for p in poi:
                gen_map[3].append((p[0]+x, p[1]+y))

        if len(gen_map) > 1:
            self.current_map, self.map_desc = gen_map[0], gen_map[1]
        else:
            self.current_map, self.map_desc = gen_map[0], [[ 0 for _ in range(len(gen_map[0][0]))] for _ in range(len(gen_map[0]))]
        if len(gen_map) > 2 and len(gen_map[2]) > 0:
            self.player_start_x, self.player_start_y = gen_map[2]
        else:
            self.player_start_x, self.player_start_y = random_free_tile(self.current_map)
        if len(gen_map) > 3:
            self.poi = gen_map[3]
            print("POI: " + str(self.poi))
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
        self.spawn_item_by_id("leather armor greaves")
        self.spawn_item_by_id("chainmail")
        self.spawn_item_by_id("boots")
        self.spawn_item_by_id("light wooden shield")
        self.spawn_item_by_id("helmet")

        #self.add_entity(generators.generate_monster("human", *random_free_tile(self.current_map)))

        for _ in range(num):
            self.spawn_random_monster()

        for d in dists:
            self.spawn_random_monster_dist(d)

        if self.gen_type in ["encampment", "city", "main"]:
             # test spawning on tiles with desc
             self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))
             self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))
             #self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))

        elif self.gen_type != "main":
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