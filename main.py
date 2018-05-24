#!/usr/bin/python2
# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod
from time import time

# save/load
import os
import game_loaders

import constants
import tileset
import renderer
import components
import generators

import level
import hud
import main_menu
import calendar
import events
import game_vars
import square_fov

from map_common import map_make_fov, map_check_for_creature, find_free_grid_in_range

import handle_input
from game_states import GameStates


class obj_Game(object):
    """Object that is basically here to communicate with the game variables"""
    def __init__(self, basic, init_seed=10):
        if not basic:
            game_vars.init_seed = self.initialize_seed(init_seed)
            data = level.load_level_data(constants.STARTING_MAP)
            if data is not None:
                game_vars.level = level.obj_Level(data[0], init_seed, False)
                game_vars.level.generate_items_monsters(data[1], data[2])
            else:
                game_vars.level = level.obj_Level(constants.STARTING_MAP, init_seed, False)
                game_vars.level.generate_items_monsters(6)

            game_vars.fov_map = map_make_fov(game_vars.level.current_map, False)

            game_vars.ai_fov_map = map_make_fov(game_vars.level.current_map, True)

            game_vars.calendar_game = calendar.obj_Calendar(1371)

            # init game object for submodules
            components.initialize_game(self)


            # use events for messages
            events.subscribers.append(self.events_handler)

        game_vars.fov_recompute = False


    @staticmethod
    def initialize_seed(seed=10):
        init_seed = seed
        print("Init seed: " + str(init_seed))
        return init_seed

    def events_handler(self, event):
        if event.type == "MESSAGE":
            self.game_message(event.data)
        elif event.type == "END_TURN":
            self.end_player_turn()

    @staticmethod
    def game_message(event_data):  # msg, msg_color, details=None):
        if len(event_data) > 2:
            game_vars.message_history.append((event_data[0], event_data[1], event_data[2]))
        else:
            game_vars.message_history.append((event_data[0], event_data[1], None))

    @staticmethod
    def add_faction(faction_data):
        game_vars.factions.append(faction_data)
        print "Added faction " + str(faction_data)
        # add the reverse mapping, too
        game_vars.factions.append((faction_data[1], faction_data[0], faction_data[2]))
        print "Added reverse faction " + str((faction_data[1], faction_data[0], faction_data[2]))

    @staticmethod
    def get_faction_reaction(faction, target_faction, log):
        if faction == target_faction:
            return 100

        for fact in game_vars.factions:
            if fact[0] == faction and fact[1] == target_faction:
                if log:
                    print("Faction reaction of " + fact[0] + " to " + fact[1] + " is " + str(fact[2]))
                return fact[2]

    @staticmethod
    def end_player_turn():
        # toggle game state to enemy turn
        game_vars.game_state = GameStates.ENEMY_TURN

    @staticmethod
    def set_player_turn():
        # set state to player turn
        game_vars.game_state = GameStates.PLAYER_TURN
        print("Set player turn")

    @staticmethod
    def map_calculate_fov():
        if game_vars.fov_recompute:
            game_vars.fov_recompute = False
            radius = PLAYER.creature.get_light_radius()

            square_fov.recompute_fov(game_vars.fov_map, PLAYER.x, PLAYER.y, radius)


            # if radius > 1:
            #     libtcod.map_compute_fov(game_vars.fov_map, PLAYER.x, PLAYER.y, radius, constants.FOV_LIGHT_WALLS,
            #                             constants.FOV_ALGO)
            # # radius 1, we want to see in all directions, use a square fov instead of whatever is defined in constants
            # else:
            #     libtcod.map_compute_fov(game_vars.fov_map, PLAYER.x, PLAYER.y, 1,
            #                             constants.FOV_LIGHT_WALLS, libtcod.FOV_PERMISSIVE_6)
    @staticmethod
    def new_level_set():
        # add player
        game_vars.level.current_entities.append(PLAYER)

        # place player in sensible place
        PLAYER.creature.move_to_target(game_vars.level.player_start_x, game_vars.level.player_start_y, game_vars.level.current_map)

        # add stuff
        game_vars.level.generate_items_monsters()

        # global FOV_MAP
        game_vars.fov_map = map_make_fov(game_vars.level.current_map, False)
        # global AI_FOV_MAP
        game_vars.ai_fov_map = map_make_fov(game_vars.level.current_map, True)

        # force fov recompute
        game_vars.fov_recompute = True
        game_vars.redraw = True

        CAMERA.start_update(PLAYER)

    def next_level(self):
        events.notify(events.GameEvent("MESSAGE", ("You descend deeper in the dungeon", "violet")))

        # make next level
        game_vars.level = level.obj_Level("cavern")

        self.new_level_set()

    def previous_level(self, from_level):
        print("From level: " + str(from_level))
        events.notify(events.GameEvent("MESSAGE", ("You ascend back", "violet")))

        # re-make starting level from seed
        data = level.load_level_data(constants.STARTING_MAP)
        if data is not None:
            game_vars.level = level.obj_Level(data[0], game_vars.init_seed, False)
            game_vars.level.generate_items_monsters(data[1], data[2])
        else:
            game_vars.level = level.obj_Level(constants.STARTING_MAP, game_vars.init_seed, False)
            game_vars.level.generate_items_monsters(6)

        self.new_level_set()

        # move to down stairs
        if from_level == "cavern":
            if hasattr(game_vars.level, 'rooms'):
                stairs_room = game_vars.level.rooms[len(game_vars.level.rooms) - 1]
                stairs_x, stairs_y = (stairs_room.x1 + stairs_room.x2 - 1) // 2, (stairs_room.y1 + stairs_room.y2 - 1) // 2
            else:
                # crash prevention
                stairs_x, stairs_y = (0,0)

            print("Move to " + str(stairs_x) + " " + str(stairs_y))
            PLAYER.creature.move_to_target(stairs_x, stairs_y, game_vars.level.current_map)

            # force fov recompute
            game_vars.fov_recompute = True
            game_vars.redraw = True

            CAMERA.start_update(PLAYER)


class obj_Camera(object):
    def __init__(self):
        self.width = 20  # 80 # blt.state(blt.TK_CELL_WIDTH)*80
        self.height = 20  # 25 # blt.state(blt.TK_CELL_HEIGHT)*25
        self.x, self.y = (0,0)
        self.top_x, self.top_y = (0,0)
        self.offset = (0,0)
        #self.rectangle = Rect(self.top_x, self.top_y, self.width, self.height)

    def start_update(self, player):
        target_pos = (80,20)
        cur_pos_x, cur_pos_y = iso_pos(player.x, player.y)
        self.offset = (target_pos[0] - cur_pos_x, target_pos[1] - cur_pos_y)
    
    def update(self):
        # this calculates cells
        self.x, self.y = PLAYER.x, PLAYER.y  # renderer.draw_iso(PLAYER.x, PLAYER.y)
        self.top_x, self.top_y = self.x - self.width/2, self.y - self.height/2
        # update rect
        #self.rectangle.update(self.top_x, self.top_y, self.width, self.height)

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

    # camera extents to speed up rendering
    def get_width_start(self):
        if self.top_x > 0:
            return self.top_x
        else:
            return 0

    def get_width_end(self, map_draw):
        if self.top_x + self.width <= len(map_draw): #constants.MAP_WIDTH:
            return self.top_x + self.width
        else:
            return len(map_draw) #constants.MAP_WIDTH

    def get_height_start(self):
        if self.top_y > 0:
            return self.top_y
        else:
            return 0

    def get_height_end(self, map_draw):
        if self.top_y + self.height <= len(map_draw[0]): #constants.MAP_HEIGHT:
            return self.top_y + self.height
        else:
            return len(map_draw[0]) #constants.MAP_HEIGHT

def death_player(player):
    events.notify(events.GameEvent("MESSAGE", (player.creature.name_instance + " is dead!", "dark red")))
    # remove from map
    game_vars.level.current_entities.remove(player)
    # set game state to player dead
    game_vars.game_state = GameStates.PLAYER_DEAD
    #delete savegame (this assumes we can only have one)
    if os.path.isfile('savegame.json'):
        os.remove('savegame.json')


# the core drawing function
def draw_game():
    # don't draw map and NPCs if sleeping
    if not PLAYER.creature.player.resting:
        blt.layer(0)
        renderer.draw_map(game_vars.level.current_map, game_vars.level.current_explored, game_vars.fov_map, constants.DEBUG)

        # moved outside since it has to be redrawn always
        #renderer.draw_mouseover(x, y)

        #blt.color("white")
        blt.color(4294967295)
        blt.layer(2)
        width_start = CAMERA.get_width_start()
        width_end = CAMERA.get_width_end(game_vars.level.current_map)
        height_start = CAMERA.get_height_start()
        height_end = CAMERA.get_height_end(game_vars.level.current_map)

        labels = game_vars.labels

        for ent in game_vars.level.current_entities:
            if ent.x >= width_start and ent.x < width_end:
                if ent.y >= height_start and ent.y < height_end:
                    ent.draw(fov_map=game_vars.fov_map)

                    if labels:
                        ent.draw_label()

    else:
        blt.puts(80,20, "SLEEPING...")



    blt.color(4294967295)

    if game_vars.game_state == GameStates.PLAYER_DEAD:
        blt.puts(80, 20, "You are dead!")


def cell_to_iso(x,y):
    offset_x = constants.MAP_WIDTH * 4
    iso_x = y / constants.TILE_HEIGHT + (x - offset_x) / constants.TILE_WIDTH
    iso_y = y / constants.TILE_HEIGHT - (x - offset_x) / constants.TILE_WIDTH - CAMERA.offset[1]
    return iso_x, iso_y

def iso_pos(x,y):
    # isometric
    offset_x = constants.CAMERA_OFFSET
    #hw = constants.HALF_TILE_WIDTH
    #hh = constants.HALF_TILE_HEIGHT
    tile_x = (x - y) * constants.HALF_TILE_WIDTH + offset_x
    tile_y = (x + y) * constants.HALF_TILE_HEIGHT
    return tile_x, tile_y


# main loop
def game_main_loop():
    """
    Main loop:
    1. fps
    2. mouse
    3. draw (including things dependent on mouse position)
        * redraw hud always
        * redraw map only if told to (basically only if moved)
    4. handle input
    5. process turns
    """

    game_quit = False

    fps_update_time = time()
    fps_counter = fps_value = 0

    while not game_quit:

        #clear
        #blt.clear()
        # hud layer
        blt.layer(1)
        blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
        # used by some menus and by effects
        blt.layer(3)
        blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))

        #blt.layer(4)
        #blt.clear_area(0,0, blt.state(blt.TK_WIDTH, blt.state(blt.TK_HEIGHT)))
        #blt.layer(5)
        #blt.clear_area(0,0,blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))

        blt.layer(0)

        if not game_vars.game_state == GameStates.MAIN_MENU:
            blt.layer(1)
            blt.puts(2,1, "[color=white]FPS: %d ms %.3f" % (fps_value, 1000/(fps_value * 1.0) if fps_value else 0) )

            #mouse
            pix_x, pix_y, _, _ = game_handle_mouse()

            # camera
            CAMERA.update()

            # draw
            if game_vars.redraw:
                blt.layer(0)
                blt.clear_area(0,0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                blt.layer(2)
                blt.clear_area(0,0,blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                if game_vars.labels:
                    blt.layer(4)
                    blt.clear_area(0, 0, blt.state(blt.TK_WIDTH, blt.state(blt.TK_HEIGHT)))
                draw_game()

            # effects
            width_start = CAMERA.get_width_start()
            width_end = CAMERA.get_width_end(game_vars.level.current_map)
            height_start = CAMERA.get_height_start()
            height_end = CAMERA.get_height_end(game_vars.level.current_map)

            for ef in game_vars.level.current_effects:

                ef.update()
                if not ef.render:
                    game_vars.level.current_effects.remove(ef)

                if ef.x >= width_start and ef.x < width_end:
                    if ef.y >= height_start and ef.y < height_end:
                        ef.draw()

            # on top of map
            blt.layer(1)
            renderer.draw_messages(game_vars.message_history)

            blt.layer(1)
            renderer.draw_mouseover(pix_x, pix_y)
            blt.color(4294967295)

            hud.draw_hud(pix_x, pix_y)

        # refresh term
        blt.refresh()

        if not game_vars.game_state == GameStates.MAIN_MENU:
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

            if player_action == "QUIT":
                game_quit = True
                break
            else:
                GAME.map_calculate_fov()


            if player_action == "mouse_click":
                print "Click"

            if player_action is not None and player_action not in ["no-action", "mouse_click", "redraw"]:
                game_vars.redraw = True
               # print("Advancing time")
                # advance time
                game_vars.calendar_game.turn += 1

                #toggle game state to enemy turn
                game_vars.game_state = GameStates.ENEMY_TURN
            elif player_action == "redraw":
                game_vars.redraw = True
            else:
                game_vars.redraw = False

            # enemy turn
            if game_vars.game_state == GameStates.ENEMY_TURN:
                for ent in game_vars.level.current_entities:
                    if ent.ai:
                        ent.ai.take_turn(PLAYER, game_vars.ai_fov_map)

                        if game_vars.game_state == GameStates.PLAYER_DEAD:
                            print("Player's dead, breaking the loop")
                            break

                if not game_vars.game_state == GameStates.PLAYER_DEAD:
                    game_vars.game_state = GameStates.PLAYER_TURN
                    # resting (potentially other stuff)
                    PLAYER.creature.player.act()
                    # test passage of time
                    #print(GAME.calendar.get_time_date(GAME.calendar.turn))

            if game_vars.game_state == GameStates.PLAYER_DEAD:
                print("PLAYER DEAD")
            #if GAME.game_state == GameStates.PLAYER_TURN:
            #    print("PLAYER TURN")

    #save if not dead
    if not game_vars.game_state == GameStates.PLAYER_DEAD and not game_vars.game_state == GameStates.MAIN_MENU:
        #print(str(GAME.game_state) + " we should save game")
        game_loaders.save_game(GAME, CAMERA, PLAYER)

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

def generate_player():
    container_com1 = components.com_Container()
    player_array = generators.generate_stats("heroic")

    player_com1 = components.com_Player()
    creature_com1 = components.com_Creature("Player", hp=20,
                                            base_str=player_array[0], base_dex=player_array[1],
                                            base_con=player_array[2],
                                            base_int=player_array[3], base_wis=player_array[4],
                                            base_cha=player_array[5],
                                            player=player_com1, faction="player", death_function=death_player)

    # body parts
    creature_com1.set_body_parts(generators.generate_body_types())


    # check that x,y isn't taken
    x,y = game_vars.level.player_start_x, game_vars.level.player_start_y
    taken = map_check_for_creature(x,y)
    if taken is not None:
        print("Looking for grid in range")
        grids = find_free_grid_in_range(3, x, y)
        #grids = find_grid_in_range(3, x,y)
        if grids is not None:
            x,y = grids[0]
        else:
            print("No grids found")
    else:
        print("No creature at " + str(x) + " " + str(y))

    player = components.obj_Actor(x, y, "@", "Player", creature=creature_com1,
                                  container=container_com1)
    
    # give starting equipment
    start_equip = generators.generate_item("longsword", x, y)
    start_equip.item.pick_up(player)
    start_equip.equipment.equip(player)
    start_equip = generators.generate_item("leather armor", x, y)
    start_equip.item.pick_up(player)
    start_equip.equipment.equip(player)
    start_equip = generators.generate_item("torch", x, y)
    start_equip.item.pick_up(player)

    return player


def start_new_game(seed):
    # in case we want to visualize the first level as it's generated
    camera = obj_Camera()
    # init camera for renderer
    renderer.initialize_camera(camera)
    game_vars.camera = camera

    game_obj = obj_Game(False, seed)

    # init factions
    game_obj.add_faction(("player", "enemy", -100))
    game_obj.add_faction(("player", "neutral", 0))

    # spawn player
    player = generate_player()

    # handle input needs all three
    handle_input.initialize_game(game_obj)
    handle_input.initialize_player(player)
    handle_input.initialize_camera(camera)

    hud.initialize_player(player)

    # adjust camera position so that player is centered
    camera.start_update(player)

    # put player last
    game_vars.player = player
    game_vars.level.current_entities.append(player)

    # test
    generators.get_random_item()

    return game_obj, player, camera

def game_initialize():
    global GAME, PLAYER, CAMERA

    blt.open()
    # default terminal size is 80x25
    blt.set("window: size=160x45, cellsize=8x16, title='Veins of the Earth'; font: default")
    # use the full version of Fixedsys Excelsior because we need arrows
    blt.set("font:font/FSEX300.ttf, size=8x16")

    #vsync
    blt.set("output.vsync=true")

    # mouse
    blt.set("input.filter={keyboard, mouse+}")
    blt.set("input: precise-mouse=true, mouse-cursor=true")

    blt.composition(True)

    # needed to avoid insta-close
    blt.refresh()

    # menu background
    blt.set("0xE100: gfx/Veins.png")

    # tiles
    tileset.set_tiles()

    # main menu
    GAME = obj_Game(True)
    game_vars.game_state = GameStates.MAIN_MENU

    ret = main_menu.main_menu_outer(start_new_game)
    if ret is not False and ret is not None:
        GAME, PLAYER, CAMERA = ret[0], ret[1], ret[2]
    else:
        # quit
        blt.close()

    # fix issue where the map is black on turn 1
    GAME.map_calculate_fov()

if __name__ == '__main__':

    game_initialize()
    game_main_loop()


