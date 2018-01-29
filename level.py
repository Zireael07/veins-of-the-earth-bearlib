import constants
import components
import generators


from map_common import get_free_tiles, random_free_tile, random_free_tile_away, random_tile_with_desc, \
    print_map_string

from bspmap import BspMapGenerator
from bspcity import BspCityGenerator
from cavemap import CaveGenerator

# need a reference to global GAME %^$@
def initialize_game(game):
    print("[Level] initialized game")
    global GAME
    GAME = game


class obj_Level(object):
    def __init__(self, gen_type="dungeon"):
        self.gen_type = gen_type
        # map gen
        if gen_type == "dungeon":
            map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                  constants.FULL_ROOMS)
        elif gen_type == "encampment":
            map_gen = BspCityGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE+2, 2,
                                False)
        elif gen_type == "city":
            map_gen = BspCityGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE+2, 2,
                                False, True)
        elif gen_type == "cavern":
            map_gen = CaveGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT)
        # fallback
        else:
            map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                      constants.FULL_ROOMS)

        gen_map = map_gen.generate_map()
        # catch degenerate instances
        if gen_type == "cavern":
            max_tiles = constants.MAP_WIDTH * constants.MAP_WIDTH
            while len(get_free_tiles(gen_map[0])) < max_tiles / 8:  # 50:
                print("Free tiles check failed, regenerating...")
                gen_map = map_gen.generate_map()

        if len(gen_map) > 1:
            self.current_map, self.map_desc = gen_map[0], gen_map[1]
        else:
            self.current_map, self.map_desc = gen_map[0], [[ 0 for _ in range(constants.MAP_HEIGHT)] for _ in range(constants.MAP_WIDTH)]
        if len(gen_map) > 2:
            self.player_start_x, self.player_start_y = gen_map[2], gen_map[3]
        else:
            self.player_start_x, self.player_start_y = random_free_tile(self.current_map)
        if len(gen_map) > 4:
            self.rooms = gen_map[4]

        # debug
        print_map_string(self.current_map)

        # new way of storing explored info
        self.current_explored = [[False for _ in range(0, constants.MAP_HEIGHT)] for _ in range(0, constants.MAP_WIDTH)]

        self.current_entities = []

        # cache the isometric calculations instead of doing them every frame
        # this wouldn't be necessary for a non-iso game since the calculations would be almost nonexistent
        self.render_positions = [[iso_pos(x,y) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]

    def add_entity(self, entity):
        if entity is not None:
            self.current_entities.append(entity)

    def spawn_random_monster(self):
        self.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(self.current_map)))

    def spawn_random_monster_dist(self, dist):
        self.add_entity(generators.generate_monster(generators.generate_random_mon(),
                                *random_free_tile_away(self.current_map, dist, (self.player_start_x, self.player_start_y))))

    def spawn_item_by_id(self, id):
        item = generators.generate_item(id, *random_free_tile(self.current_map))
        self.add_entity(item)
        if item:
            item.send_to_back()



    def generate_items_monsters(self):
        # test potion
        x, y = random_free_tile(self.current_map)
        item_com = components.com_Item(use_function=cast_heal)
        item = components.obj_Actor(x, y, 0x2762, "potion", item=item_com)
        self.current_entities.append(item)
        item.send_to_back()

        # test generating items
        self.spawn_item_by_id("longsword")
        self.spawn_item_by_id("dagger")
        self.spawn_item_by_id("studded armor")
        self.spawn_item_by_id("chainmail")

        self.add_entity(generators.generate_monster("human", *random_free_tile(self.current_map)))

        if self.gen_type == "encampment" or self.gen_type == "city":
            # test generating monsters
            self.spawn_random_monster_dist(6)
            self.spawn_random_monster_dist(6)
            self.spawn_random_monster_dist(6)
            self.spawn_random_monster_dist(6)
            self.spawn_random_monster_dist(6)
            self.spawn_random_monster_dist(6)
            self.spawn_random_monster_dist(6)

            # test spawning on tiles with desc
            self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))
            self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))
            self.add_entity(generators.generate_monster("human", *random_tile_with_desc(self.map_desc, 2)))

        else:
            # test: force spawn a monster on top of the player
            self.add_entity(generators.generate_monster("goblin", self.player_start_x, self.player_start_y))

            self.spawn_random_monster()
            self.spawn_random_monster()
            self.spawn_random_monster()
            self.spawn_random_monster()
            self.spawn_random_monster()
            self.spawn_random_monster_dist(4)
            self.spawn_random_monster_dist(4)

# item use effects
def cast_heal(actor):
    if actor.creature.hp == actor.creature.max_hp:
        GAME.game_message("You are already fully healed!", "red")
        return 'cancelled'

    heal = generators.roll(1,8)
    GAME.game_message("You healed " + str(heal) + " damage", "violet")
    actor.creature.heal(heal)

def iso_pos(x,y):
    # isometric
    offset_x = constants.CAMERA_OFFSET
    #hw = constants.HALF_TILE_WIDTH
    #hh = constants.HALF_TILE_HEIGHT
    tile_x = (x - y) * constants.HALF_TILE_WIDTH + offset_x
    tile_y = (x + y) * constants.HALF_TILE_HEIGHT
    return tile_x, tile_y