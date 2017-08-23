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
from map_common import map_make_fov, random_free_tile, Rect, print_map_string
from bspmap import BspMapGenerator
import handle_input
from game_states import GameStates


class obj_Game(object):
    def __init__(self):
        #self.current_map = map_create()
        map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                  constants.FULL_ROOMS)
        self.current_map, self.player_start_x, self.player_start_y, self.rooms = map_gen.generate_map()

        print_map_string(self.current_map)

        global FOV_MAP
        FOV_MAP = map_make_fov(self.current_map)

        # new way of storing explored info
        self.current_explored = [[ False for _ in range(0, constants.MAP_HEIGHT)] for _ in range(0, constants.MAP_WIDTH)]

        self.current_entities = []
        self.factions = []

        self.message_history = []
        self.fov_recompute = False

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

    def next_level(self):
        self.game_message("You descend deeper in the dungeon", "violet")

        # make next level
        map_gen = BspMapGenerator(constants.MAP_WIDTH, constants.MAP_HEIGHT, constants.ROOM_MIN_SIZE, constants.DEPTH,
                                  constants.FULL_ROOMS)
        self.current_map, self.player_start_x, self.player_start_y, self.rooms = map_gen.generate_map()

        print_map_string(self.current_map)

        global FOV_MAP
        FOV_MAP = map_make_fov(self.current_map)

        # force fov recompute
        self.fov_recompute = True

class obj_Camera(object):
    def __init__(self):
        self.width = 20  # 80 # blt.state(blt.TK_CELL_WIDTH)*80
        self.height = 20  # 25 # blt.state(blt.TK_CELL_HEIGHT)*25
        self.x, self.y = (0,0)
        self.top_x, self.top_y = (0,0)
        self.offset = (0,0)
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


def death_player(player):
    GAME.game_message(player.creature.name_instance + " is dead!", "dark red")
    # remove from map
    GAME.current_entities.remove(player)
    # set game state to player dead
    GAME.game_state = GameStates.PLAYER_DEAD

def map_create():
    #new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]
    new_map = [[ 0 for _ in range(0, constants.MAP_HEIGHT)] for _ in range(0, constants.MAP_WIDTH)]


    new_map[10][10] = 0 #.block_path = True
    new_map[12][12] = 0 #.block_path = True

    # walls around the map
    for x in range(constants.MAP_WIDTH):
        new_map[x][0] = 0 #.block_path = True
        new_map[x][constants.MAP_WIDTH-1] = 0 #.block_path = True

    for y in range(constants.MAP_HEIGHT):
        new_map[0][y] = 0 #.block_path = True
        new_map[constants.MAP_HEIGHT-1][y] = 0 #.block_path = True

    return new_map


def map_calculate_fov():
    if GAME.fov_recompute:
        GAME.fov_recompute = False
        libtcod.map_compute_fov(FOV_MAP, PLAYER.x, PLAYER.y, constants.LIGHT_RADIUS, constants.FOV_LIGHT_WALLS,
                                constants.FOV_ALGO)


# the core drawing function
def draw_game(x,y):
    renderer.draw_map(GAME.current_map, GAME.current_explored, FOV_MAP)

    renderer.draw_mouseover(x,y)

    #blt.color("white")
    blt.color(4294967295)
    for ent in GAME.current_entities:
        ent.draw(fov_map=FOV_MAP)

    # on top of map
    blt.layer(1)
    renderer.draw_messages(GAME.message_history)

    renderer.draw_bar(2, 15, 20, "HP", PLAYER.creature.hp, PLAYER.creature.max_hp, "red", "darker red", str(PLAYER.creature.hp))
    blt.color(4294967295)



def cell_to_iso(x,y):
    offset_x = constants.MAP_WIDTH * 4
    iso_x = y / constants.TILE_HEIGHT + (x - offset_x) / constants.TILE_WIDTH
    iso_y = y / constants.TILE_HEIGHT - (x - offset_x) / constants.TILE_WIDTH - CAMERA.offset[1]
    return iso_x, iso_y



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

def get_top_log_string_index():
    # msg_num = -constants.NUM_MESSAGES
    check = -4
    # print("Checking " + str(check))

    if not GAME.message_history:
        return None

    if len(GAME.message_history) < 4:
        check = -len(GAME.message_history)

    if GAME.message_history[check]:
        return check

# save/load
def save_game():
    data = {
        'serialized_player_index': jsonpickle.encode(GAME.current_entities.index(PLAYER)),
        'serialized_cam': jsonpickle.encode(CAMERA),
        'serialized_game': jsonpickle.encode(GAME),
    }

    #test
    print data['serialized_player_index']

    # write to file
    with open('savegame.json', 'w') as save_file:
        json.dump(data, save_file, indent=4)

def load_game():
    with open('savegame.json', 'r') as save_file:
        data = json.load(save_file)

    game = jsonpickle.decode(data['serialized_game'])
    player_index = jsonpickle.decode(data['serialized_player_index'])
    camera = jsonpickle.decode(data['serialized_cam'])

    player = game.current_entities[player_index]

    return game, player, camera


# main loop
def game_main_loop():
    game_quit = False

    fps_update_time = time()
    fps_counter = fps_value = 0

    while not game_quit:

        #clear
        blt.clear()

        blt.layer(1)
        blt.puts(2,1, "[color=white]FPS: %d" % (fps_value))

        #mouse
        pix_x, pix_y, m_x, m_y = game_handle_mouse()

        # camera
        CAMERA.update()

        # draw
        draw_game(pix_x, pix_y)

        # debug
        #on top of map
        blt.layer(1)
        blt.puts(2,2, "[color=red] player position: %d %d" % (PLAYER.x, PLAYER.y))
        blt.puts(2,5, "[color=red] camera offset: %d %d" % (CAMERA.offset[0], CAMERA.offset[1]))
        # debugging rooms
        blt.puts(2,6, "[color=orange] room index: %s" % (room_index_str()))
        blt.puts(2,7, "[color=orange] room center %s" % (get_room_data()))

        # this works on cells
        blt.layer(0)
        mouse_picking(m_x, m_y)

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

            player_action = handle_input.game_handle_keys()
            #print player_action

            map_calculate_fov()

            if player_action == "QUIT":
                game_quit = True


            if player_action == "mouse_click":
                print "Click"


            if player_action != "no-action" and player_action != "mouse_click":
                #toggle game state to enemy turn
                GAME.game_state = GameStates.ENEMY_TURN

            # enemy turn
            if GAME.game_state == GameStates.ENEMY_TURN:
                for ent in GAME.current_entities:
                    if ent.ai:
                        ent.ai.take_turn(PLAYER)

                        if GAME.game_state == GameStates.PLAYER_DEAD:
                            print("Player's dead, breaking the loop")
                            break

                if not GAME.game_state == GameStates.PLAYER_DEAD:
                    GAME.game_state = GameStates.PLAYER_TURN

            if GAME.game_state == GameStates.PLAYER_DEAD:
                print("PLAYER DEAD")
            #if GAME.game_state == GameStates.PLAYER_TURN:
            #    print("PLAYER TURN")
    #save
    save_game()

    # quit the game
    blt.close()


# mouse movement
def game_handle_mouse():
    # values
    m_x = blt.state(blt.TK_MOUSE_X)
    m_y = blt.state(blt.TK_MOUSE_Y)
    pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
    pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)

    # mouse test
    blt.layer(1)
    blt.puts(
        3, 4,
        "Cursor: [color=orange]%d:%d[/color] [color=dark gray]cells[/color]"
        ", [color=orange]%d:%d[/color] [color=dark gray]pixels[/color]" % (
            m_x,
            m_y,
            pix_x,
            pix_y))

    # map tile picking
    # fake an offset of camera offset * cell width
    pix_x = pix_x - CAMERA.offset[0] * blt.state(blt.TK_CELL_WIDTH)

    # fake an offset of camera offset * cell height
    pix_y = pix_y - CAMERA.offset[1] * blt.state(blt.TK_CELL_HEIGHT)

    blt.puts(2, 3, "[color=red] iso coords based on pixels: %d %d" % (renderer.pix_to_iso(pix_x, pix_y)))
    blt.layer(0)

    return pix_x, pix_y, m_x, m_y

def mouse_picking(m_x, m_y):
    # log_h = blt.state(blt.TK_HEIGHT) - (constants.NUM_MESSAGES)
    # mouse picking test
    w = 4
    h = 9

    n = 0
    while True:
        # detect mousing over message log
        #if m_x < 40 and m_y >= log_h:
        #    break

        code = blt.pick(m_x, m_y, n)

        if code == 0: break

        blt.layer(1)
        blt.puts(w + n * 2, h, u"%c" % (code))
        blt.layer(0)
        n += 1
        #
        if n == 0:
            blt.puts(w, h, "Empty cell")



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

    # init game for submodules
    components.initialize_game(game)
    generators.initialize_game(game)
    renderer.initialize_game(game)

    # init factions
    game.add_faction(("player", "enemy", -100))
    game.add_faction(("player", "neutral", 0))

    container_com1 = components.com_Container()
    player_array = generators.generate_stats("heroic")
    creature_com1 = components.com_Creature("Player", hp=20,
                                            base_str=player_array[0], base_dex=player_array[1],
                                            base_con=player_array[2],
                                            base_int=player_array[3], base_wis=player_array[4],
                                            base_cha=player_array[5],
                                            player=True, faction="player", death_function=death_player)

    player = components.obj_Actor(game.player_start_x, game.player_start_y, "@", "Player", creature=creature_com1,
                                  container=container_com1)

    camera = obj_Camera()

    # init camera for renderer
    renderer.initialize_camera(camera)

    # handle input needs all three
    handle_input.initialize_game(game)
    handle_input.initialize_player(player)
    handle_input.initialize_camera(camera)

    # adjust camera position so that player is centered
    camera.start_update(player)

    # generate items
    generate_items_monsters(game)

    # put player last
    game.current_entities.append(player)

    # test
    generators.get_random_item()

    return game, player, camera

def game_initialize():
    global GAME, PLAYER, CAMERA

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
    blt.set("0x003E: gfx/stairs_down.png, align=center") # ">"
    blt.set("0x003C: gfx/stairs_up.png, align=center") # "<"
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
        # player_id = len(GAME.current_entities)-1
        # the assumption isn't true if you pick up and drop some items
        # so we handle it in load_game()
        #GAME.current_entities[player_id] = PLAYER

        # handle FOV
        GAME.fov_recompute = True
        # recreate the fov
        global FOV_MAP
        FOV_MAP = map_make_fov(GAME.current_map)

        # patch in required stuff
        # init game for submodules
        components.initialize_game(GAME)
        generators.initialize_game(GAME)
        renderer.initialize_game(GAME)

        # init camera for renderer
        renderer.initialize_camera(CAMERA)

        #handle input needs all three
        handle_input.initialize_game(GAME)
        handle_input.initialize_player(PLAYER)
        handle_input.initialize_camera(CAMERA)

        # we don't have to reset camera position because it's loaded from the file
        #CAMERA.start_update(PLAYER)

        # fix issue where the map is black on turn 1
        map_calculate_fov()

        print("Game loaded")

        # set state to player turn
        GAME.game_state = GameStates.PLAYER_TURN

    else:
        GAME, PLAYER, CAMERA = start_new_game()
        GAME.fov_recompute = True
        # fix issue where the map is black on turn 1
        map_calculate_fov()

        #set state to player turn
        GAME.game_state = GameStates.PLAYER_TURN

if __name__ == '__main__':

    game_initialize()
    game_main_loop()


