# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod
from time import time
# save/load
import jsonpickle
import json
import os

import constants
import renderer
import components
import generators
from map_common import struc_Tile, map_make_fov, random_free_tile, Rect, print_map_string
from bspmap import BspMapGenerator

class obj_Game(object):
    def __init__(self):
        #self.current_map = map_create()
        map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                  constants.FULL_ROOMS)
        self.current_map, self.player_start_x, self.player_start_y, self.rooms = map_gen.generate_map()

        print_map_string(self.current_map)

        global FOV_MAP
        FOV_MAP = map_make_fov(self.current_map)

        self.current_entities = []
        self.factions = []

        self.message_history = []

    def game_message(self, msg, msg_color):
        self.message_history.append((msg, msg_color))

    def add_entity(self, entity):
        if entity is not None:
            self.current_entities.append(entity)

    def add_faction(self, faction_data):
        self.factions.append(faction_data)
        print "Added faction " + str(faction_data)
        # add the reverse mapping, too
        self.factions.append((faction_data[1], faction_data[0], faction_data[2]))
        print "Added reverse faction " + str((faction_data[1], faction_data[0], faction_data[2]))

    def get_faction_reaction(self, faction, target_faction, log):
        if faction == target_faction:
            return 100


        for fact in self.factions:
            if fact[0] == faction and fact[1] == target_faction:
                if log:
                    print("Faction reaction of " + fact[0] + " to " + fact[1] + " is " + str(fact[2]))
                return fact[2]


class AI_test(object):
    def take_turn(self):
        self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1), GAME.current_map)


class obj_Camera(object):
    def __init__(self):
        self.width = 20  # 80 # blt.state(blt.TK_CELL_WIDTH)*80
        self.height = 20  # 25 # blt.state(blt.TK_CELL_HEIGHT)*25
        self.x, self.y = (0,0)
        self.top_x, self.top_y = (0,0)
        self.offset = (0,10) #default offset is 10 along y axis
        self.rectangle = Rect(self.top_x, self.top_y, self.width, self.height)

    def start_update(self, player):
        target_pos = (80,20)
        cur_pos_x, cur_pos_y = renderer.draw_iso(player.x, player.y)
        self.offset = (target_pos[0] - cur_pos_x, target_pos[1] - cur_pos_y)
    
    def update(self):
        # this calculates cells
        self.x, self.y = PLAYER.x, PLAYER.y  # renderer.draw_iso(PLAYER.x, PLAYER.y)
        self.top_x, self.top_y = self.x - self.width/2, self.y - self.height/2
        # update rect
        self.rectangle.update(self.top_x, self.top_y, self.width, self.height)

    def move(self, dx, dy):
        # print("Moving the camera by " + str(dx) + ", " + str(dy))
        # if we increase map x by 1, draw coordinates increase by 1/2 tile width, 1/2 tile height
        # reverse that since we want the camera to stay in same place
        x_change = (-constants.TILE_WIDTH/2, -constants.TILE_HEIGHT/2)
        # if we increase map y by 1, draw coordinates change by -1/2 tile_width, 1/2 tile height
        # reverse that since we want the camera to stay in one place
        y_change = (constants.TILE_WIDTH/2, -constants.TILE_HEIGHT/2)
        #print("Offset change for 1 x is " + str(x_change) + " for 1 y is " + str(y_change))
        #print("offset change for -1x is" + str((x_change[0]*-1, x_change[1]*-1)) + " for -1 y is" + str((y_change[0]*-1, y_change[1]*-1)))

        #print("Offset calculations x: " + str(self.offset[0]) + " " + str(x_change[0]*dx) + " " + str(y_change[0]*dy))
        #print("Offset calculations y: " + str(self.offset[1]) + " " + str(x_change[1]*dx) + " " + str(y_change[1]*dy))
        new_x = self.offset[0] + x_change[0]*dx + y_change[0]*dy
        new_y = self.offset[1] + x_change[1]*dx + y_change[1]*dy

        self.offset = (new_x, new_y)

    # @property
    # def rectangle(self):
    #     cam_rect = Rect(self.top_x, self.top_y, self.width, self.height)
    #     return cam_rect

# This will be used both by AI and map checking - that's why it's not in components.py
def move_astar(actor, target, inc_map):
    #Create a FOV map that has the dimensions of the map
    fov = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    #Scan the current map each turn and set all the walls as unwalkable
    for y1 in range(constants.MAP_HEIGHT):
        for x1 in range(constants.MAP_WIDTH):
            libtcod.map_set_properties(fov, x1, y1, not inc_map[x1][y1].block_path, not inc_map[x1][y1].block_path)

    #Scan all the entities to see if there are objects that must be navigated around
    #Check also that the entity isn't self or the target (so that the start and the end points are free)
    #The AI class handles the situation if self is next to the target so it will not use this A* function anyway
    for ent in GAME.current_entities:
        if ent.creature and ent != actor and ent != target:
            #Set the tile as a wall so it must be navigated around
            libtcod.map_set_properties(fov, ent.x, ent.y, True, False)

    #Allocate a A* path
    #The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
    my_path = libtcod.path_new_using_map(fov, 1.41)

    #Compute the path between self's coordinates and the target's coordinates
    libtcod.path_compute(my_path, actor.x, actor.y, target.x, target.y)

    #Check if the path exists, and in this case, also the path is shorter than 25 tiles
    #The path size matters if you want the monster to use alternative longer paths (for example through other rooms) if for example the player is in a corridor
    #It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
    if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
        #Find the next coordinates in the computed full path
        x, y = libtcod.path_walk(my_path, True)
        if x or y:
            #Set self's coordinates to the next path tile
            actor.x = x
            actor.y = y
    #else:
        #Keep the old move function as a backup so that if there are no paths (for example another monster blocks a corridor)
        #it will still try to move towards the player (closer to the corridor opening)
     #   self.move_towards(target.x, target.y)

    #Delete the path to free memory
    libtcod.path_delete(my_path)
    
def death_monster(monster):
    GAME.game_message(monster.creature.name_instance + " is dead!", "gray")
    # clean up components
    monster.creature = None
    monster.ai = None
    # remove from map
    GAME.current_entities.remove(monster)

def map_create():
    new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]

    new_map[10][10].block_path = True
    new_map[12][12].block_path = True

    # walls around the map
    for x in range(constants.MAP_WIDTH):
        new_map[x][0].block_path = True
        new_map[x][constants.MAP_WIDTH-1].block_path = True

    for y in range(constants.MAP_HEIGHT):
        new_map[0][y].block_path = True
        new_map[constants.MAP_HEIGHT-1][y].block_path = True

    return new_map

def map_calculate_fov():
    global FOV_CALCULATE, PLAYER

    if FOV_CALCULATE:
        FOV_CALCULATE = False
        libtcod.map_compute_fov(FOV_MAP, PLAYER.x, PLAYER.y, constants.LIGHT_RADIUS, constants.FOV_LIGHT_WALLS,
                                constants.FOV_ALGO)


def map_check_for_item(x,y):
    target = None

    for ent in GAME.current_entities:
        if (ent.x == x
            and ent.y == y
            and ent.item):
            target = ent

        if target:
            return target

# the core drawing function
def draw_game(x,y):
    renderer.draw_map(GAME.current_map, FOV_MAP)

    draw_mouseover(x,y)

    #blt.color("white")
    blt.color(4294967295)
    for ent in GAME.current_entities:
        ent.draw(fov_map=FOV_MAP)

    renderer.draw_messages(GAME.message_history)


def draw_mouseover(x,y):
    tile_x, tile_y = pix_to_iso(x, y)
    draw_x, draw_y = renderer.draw_iso(tile_x, tile_y)

    blt.color("light yellow")
    blt.put(draw_x, draw_y, 0x2317)


def cell_to_iso(x,y):
    offset_x = constants.MAP_WIDTH * 4
    iso_x = y / constants.TILE_HEIGHT + (x - offset_x) / constants.TILE_WIDTH
    iso_y = y / constants.TILE_HEIGHT - (x - offset_x) / constants.TILE_WIDTH - CAMERA.offset[1]
    return iso_x, iso_y


def cell_to_pix(val, width):
    if width:
        #print("Cell width is " + str(blt.state(blt.TK_CELL_WIDTH)))
        res = val * blt.state(blt.TK_CELL_WIDTH)
    else:
        #print("Cell height is " + str(blt.state(blt.TK_CELL_HEIGHT)))
        res = val * blt.state(blt.TK_CELL_HEIGHT)
    #print("Result is " + str(res))
    return res

def pix_to_iso(x,y):
    x = float(x)
    y = float(y)
    offset_x = cell_to_pix(constants.MAP_WIDTH * 4, True)
    iso_x = y / cell_to_pix(constants.TILE_HEIGHT, False) + (x - offset_x) / cell_to_pix(constants.TILE_WIDTH, True)
    iso_y = y / cell_to_pix(constants.TILE_HEIGHT, False) - (x - offset_x) / cell_to_pix(constants.TILE_WIDTH, True)
    # iso_x = y / 27 + (x - offset_x) / 54
    # iso_y = y / 27 - (x - offset_x) / 54
    # print("Iso_x " + str(int(iso_x)) + "iso_y " + str(int(iso_y)))
    return int(iso_x), int(iso_y)


def roll(dice, sides):
     result = 0
     for i in range(0, dice, 1):
         roll = libtcod.random_get_int(0, 1, sides)
         result += roll

     print 'Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result)
     return result

# debugging rooms
def get_room_index():
    room_index = -1
    for r in GAME.rooms:

        if r.contains((PLAYER.x, PLAYER.y)):
            room_index = GAME.rooms.index(r)
            break

    return room_index

def room_index_str():
    index = get_room_index()

    if index != -1:
        return str(index)
    else:
        return "None"

def get_room_from_index(index):
    if index != -1:
        return GAME.rooms[index]

def get_room_data():
    index = get_room_index()
    if index != -1:
        room = get_room_from_index(index)
        return "Center: " + str(room.center()) + " x " + str(room.x1) + " y " + str(room.y1) +\
               " x2 " + str(room.x2) + " y2 " + str(room.y2) +\
               " width " + str(room.x2-room.x1) + " height " + str(room.y2-room.y1)
    else:
        return "None"

# save/load
def save_game():
    data = {
        'serialized_player': jsonpickle.encode(PLAYER),
        'serialized_cam': jsonpickle.encode(CAMERA),
        'serialized_game': jsonpickle.encode(GAME),
    }

    #test
    #print data['serialized_cam']

    # write to file
    with open('savegame.json', 'w') as save_file:
        json.dump(data, save_file, indent=4)

def load_game():
    with open('savegame.json', 'r') as save_file:
        data = json.load(save_file)

    game = jsonpickle.decode(data['serialized_game'])
    player = jsonpickle.decode(data['serialized_player'])
    camera = jsonpickle.decode(data['serialized_cam'])

    return game, player, camera


def game_main_loop():
    game_quit = False

    fps_update_time = time()
    fps_counter = fps_value = 0

    while not game_quit:

        #clear
        blt.clear()


        blt.puts(2,1, "[color=white]FPS: %d" % (fps_value))

        # mouse test
        blt.puts(
            3, 4,
            "Cursor: [color=orange]%d:%d[/color] [color=dark gray]cells[/color]"
            ", [color=orange]%d:%d[/color] [color=dark gray]pixels[/color]" % (
                blt.state(blt.TK_MOUSE_X),
                blt.state(blt.TK_MOUSE_Y),
                blt.state(blt.TK_MOUSE_PIXEL_X),
                blt.state(blt.TK_MOUSE_PIXEL_Y)))

        # map tile picking test
        # cell_x = blt.state(blt.TK_MOUSE_X)
        # cell_y = blt.state(blt.TK_MOUSE_Y)

        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        # fake an offset of camera offset * cell width
        pix_x = pix_x - CAMERA.offset[0]*blt.state(blt.TK_CELL_WIDTH)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)
        # fake an offset of camera offset * cell height
        pix_y = pix_y - CAMERA.offset[1]*blt.state(blt.TK_CELL_HEIGHT)

        #blt.puts(2,2, "[color=red] iso coords based on cells: %d %d" % (cell_to_iso(cell_x,cell_y)))
        blt.puts(2,3, "[color=red] iso coords based on pixels: %d %d" % (pix_to_iso(pix_x, pix_y)))

        # mouse picking test
        x = blt.state(blt.TK_MOUSE_X)
        y = blt.state(blt.TK_MOUSE_Y)

        n = 0
        while True:
             code = blt.pick(x, y, n)

             if code == 0: break

             blt.puts(2 + n * 2, 5, u"%c" % (code))
             n += 1
        #
             if n == 0:
                 blt.puts(3, 5, "Empty cell")


        # camera
        CAMERA.update()

        # draw
        draw_game(pix_x, pix_y)

        # debug
        # debug
        blt.puts(2,2, "[color=red] player position: %d %d" % (PLAYER.x, PLAYER.y))
        blt.puts(2,5, "[color=red] camera offset: %d %d" % (CAMERA.offset[0], CAMERA.offset[1]))
        # debugging rooms
        blt.puts(2,6, "[color=orange] room index: %s" % (room_index_str()))
        blt.puts(2,7, "[color=orange] room center %s" % (get_room_data()))


        # refresh term
        blt.refresh()

        # fps
        fps_counter += 1
        tm = time()
        if tm > fps_update_time + 1:
            fps_value = fps_counter
            fps_counter = 0
            fps_update_time = tm

        # avoid blocking the game with blt.read
        while not game_quit and blt.has_input():


            player_action = game_handle_keys()

            map_calculate_fov()

            if player_action == "QUIT":
                game_quit = True


            if player_action == "mouse_click":
                print "Click"


            if player_action != "no-action" and player_action != "mouse_click":
                for ent in GAME.current_entities:
                    if ent.ai:
                        ent.ai.take_turn()

    #save
    save_game()

    # quit the game
    blt.close()

def game_handle_keys():
    global FOV_CALCULATE

    key = blt.read()
    if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
        return "QUIT"

    if key == blt.TK_UP:
        if PLAYER.creature.move(0, -1, GAME.current_map):
            CAMERA.move(0, -1)
            FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_DOWN:
        if PLAYER.creature.move(0, 1, GAME.current_map):
            CAMERA.move(0,1)
            FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_LEFT:
        if PLAYER.creature.move(-1, 0, GAME.current_map):
            CAMERA.move(-1,0)
            FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_RIGHT:
        if PLAYER.creature.move(1, 0, GAME.current_map):
            CAMERA.move(1,0)
            FOV_CALCULATE = True
        return "player-moved"

    # items
    if key == blt.TK_G:
        ent = map_check_for_item(PLAYER.x, PLAYER.y)
        #for ent in objects:
        ent.item.pick_up(PLAYER)

    if key == blt.TK_D:
        if len(PLAYER.container.inventory) > 0:
            #drop the last item
            PLAYER.container.inventory[-1].item.drop(PLAYER.x, PLAYER.y)

    if key == blt.TK_I:
        chosen_item = renderer.inventory_menu("Inventory", PLAYER)
        if chosen_item is not None:
            if chosen_item.item:
                chosen_item.item.use(PLAYER)

    if key == blt.TK_C:
        renderer.character_sheet_menu("Character sheet", PLAYER)

    if key == blt.TK_GRAVE and blt.check(blt.TK_SHIFT):
        print("Debug mode on")
        constants.DEBUG = True

    # mouse

    if key == blt.TK_MOUSE_LEFT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)

        # fake an offset of camera offset * cell width
        pix_x = pix_x - CAMERA.offset[0] * blt.state(blt.TK_CELL_WIDTH)

        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)

        # fake an offset of camera offset * cell height
        pix_y = pix_y - CAMERA.offset[1] * blt.state(blt.TK_CELL_HEIGHT)

        click_x, click_y = pix_to_iso(pix_x, pix_y)

        print "Clicked on tile " + str(click_x) + " " + str(click_y)

        if click_x != PLAYER.x or click_y != PLAYER.y:
            moved = PLAYER.creature.move_towards(click_x, click_y, GAME.current_map)
            if (moved[0]):
                CAMERA.move(moved[1], moved[2])
                FOV_CALCULATE = True

        return "player-moved"

    if  key == blt.TK_MOUSE_RIGHT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)
        print "Right clicked on tile " + str(pix_to_iso(pix_x, pix_y))

        return "mouse_click"


    return "no-action"


def generate_items_monsters(game):
    # test generating items
    game.current_entities.append(generators.generate_item("longsword", *random_free_tile(game.current_map)))
    game.current_entities.append(generators.generate_item("dagger", *random_free_tile(game.current_map)))
    game.current_entities.append(generators.generate_item("chainmail", *random_free_tile(game.current_map)))

    game.add_entity(generators.generate_monster("human", *random_free_tile(game.current_map)))
    # test generating monsters
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))
    game.add_entity(generators.generate_monster(generators.generate_random_mon(), *random_free_tile(game.current_map)))


def start_new_game():
    game = obj_Game()

    fov = True

    # init game for submodules
    components.initialize_game(game)
    generators.initialize_game(game)

    # init factions
    game.add_faction(("player", "enemy", -100))
    game.add_faction(("player", "neutral", 0))

    container_com1 = components.com_Container()
    player_array = generators.generate_stats("heroic")
    creature_com1 = components.com_Creature("Player",
                                            base_str=player_array[0], base_dex=player_array[1],
                                            base_con=player_array[2],
                                            base_int=player_array[3], base_wis=player_array[4],
                                            base_cha=player_array[5],
                                            faction="player")

    player = components.obj_Actor(game.player_start_x, game.player_start_y, "@", "Player", creature=creature_com1,
                                  container=container_com1)

    camera = obj_Camera()

    # init camera for renderer
    renderer.initialize_camera(camera)

    # adjust camera position so that player is centered
    camera.start_update(player)

    # generate items
    generate_items_monsters(game)

    # put player last
    game.current_entities.append(player)

    # test
    generators.get_random_item()

    return game, fov, player, camera

def game_initialize():
    global GAME, FOV_CALCULATE, PLAYER, CAMERA

    blt.open()
    # default terminal size is 80x25
    blt.set("window: size=160x45, cellsize=auto, title='Veins of the Earth'; font: default")

    #vsync
    blt.set("output.vsync=true")

    # mouse
    blt.set("input.filter={keyboard, mouse+}")
    blt.set("input: precise-mouse=true, mouse-cursor=true")

    blt.composition(True)

    # needed to avoid insta-close
    blt.refresh()

    # tiles
    blt.set("0x3002: gfx/floor_sand.png, align=center") # "."
    blt.set("0x23: gfx/wall_stone.png, align=center") # "#"
    blt.set("0x40: gfx/human_m.png, align=center") # "@"
    #NPCs (we use Unicode private area here)
    blt.set("0xE000: gfx/kobold.png,  align=center") # ""
    blt.set("0xE001: gfx/goblin.png, align=center")
    blt.set("0xE002: gfx/drow_fighter.png, align=center")
    blt.set("0xE003: gfx/human.png, align=center")
    #items
    blt.set("0x2215: gfx/longsword.png, align=center") #"∕"
    blt.set("0x1C0: gfx/dagger.png, align=center") # "ǀ"
    blt.set("0xFF3B: gfx/chain_armor.png, align=center") # "［"

    # gfx
    blt.set("0x2317: gfx/mouseover.png, align=center") # "⌗"
    blt.set("0x2017: gfx/unit_marker.png, align=center") # "̳"

    # if we have a savegame, load it
    if os.path.isfile('savegame.json'):
        GAME, PLAYER, CAMERA = load_game()

        # fix player ref
        # player is always last in the entities list
        player_id = len(GAME.current_entities)-1
        GAME.current_entities[player_id] = PLAYER

        # handle FOV
        FOV_CALCULATE = True
        # recreate the fov
        global FOV_MAP
        FOV_MAP = map_make_fov(GAME.current_map)

        # patch in required stuff
        # init game for submodules
        components.initialize_game(GAME)
        generators.initialize_game(GAME)

        # init camera for renderer
        renderer.initialize_camera(CAMERA)

        # adjust camera position so that player is centered
        CAMERA.start_update(PLAYER)

        # fix issue where the map is black on turn 1
        map_calculate_fov()

    else:
        GAME, FOV_CALCULATE, PLAYER, CAMERA = start_new_game()
        # fix issue where the map is black on turn 1
        map_calculate_fov()

if __name__ == '__main__':

    game_initialize()
    game_main_loop()


