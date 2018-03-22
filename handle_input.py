from bearlibterminal import terminal as blt

import constants
from game_states import GameStates
import gui_menus
from renderer import pix_to_iso
from map_common import map_check_for_items, find_unexplored_closest
from tile_lookups import TileTypes, get_index

import game_vars

def initialize_camera(camera):
    global CAMERA
    CAMERA = camera

def initialize_game(game):
    global GAME
    GAME = game

def initialize_player(player):
    global PLAYER
    PLAYER = player

# nowhere else to put it?
def get_top_log_string_index():
    # msg_num = -constants.NUM_MESSAGES
    check = -4
    #print("Checking " + str(check))

    if not game_vars.message_history:
        return None

    if len(game_vars.message_history) < 4:
        check = -len(game_vars.message_history)


    if game_vars.message_history[check]:
        return check


def click_on_msg_log(m_y):
    log_h = blt.state(blt.TK_HEIGHT) - (constants.NUM_MESSAGES)
    # which line?
    if m_y == log_h:
        # print("Clicked over line #1")
        check = get_top_log_string_index()
        if check is not None:
            print(game_vars.message_history[check])
            gui_menus.display_dmg_window(check)

    elif m_y == log_h + 1:
        check = get_top_log_string_index()
        if check is not None:
            print(game_vars.message_history[check + 1])
            gui_menus.display_dmg_window(check + 1)

    elif m_y == log_h + 2:
        check = get_top_log_string_index()
        if check is not None:
            print(game_vars.message_history[check + 2])
            gui_menus.display_dmg_window(check + 2)
    elif m_y == log_h + 3:
        check = get_top_log_string_index()
        if check is not None:
            print(game_vars.message_history[check + 3])
            gui_menus.display_dmg_window(check + 3)


# player input
def game_handle_mouse_input(key):
    # left key
    if key == blt.TK_MOUSE_LEFT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)

        m_x = blt.state(blt.TK_MOUSE_X)
        m_y = blt.state(blt.TK_MOUSE_Y)

        # did we click over the message log?
        if m_x < 40:
            click_on_msg_log(m_y)

        # press over map
        else:
            # fake an offset of camera offset * cell width
            pix_x = pix_x - CAMERA.offset[0] * blt.state(blt.TK_CELL_WIDTH)

            # fake an offset of camera offset * cell height
            pix_y = pix_y - CAMERA.offset[1] * blt.state(blt.TK_CELL_HEIGHT)

            click_x, click_y = pix_to_iso(pix_x, pix_y)

            if click_x > 0 and click_x < constants.MAP_WIDTH - 1:
                if click_y > 0 and click_y < constants.MAP_HEIGHT - 1:
                    print "Clicked on tile " + str(click_x) + " " + str(click_y)

                    if click_x != PLAYER.x or click_y != PLAYER.y:
                        moved = PLAYER.creature.move_towards(click_x, click_y, game_vars.level.current_map)
                        if (moved[0]):
                            CAMERA.move(moved[1], moved[2])
                            game_vars.fov_recompute = True

                    return "player-moved"

    # pressed right mouse button
    if key == blt.TK_MOUSE_RIGHT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)
        print "Right clicked on tile " + str(pix_to_iso(pix_x, pix_y))

        return "mouse_click"

def game_key_move(key):
    KEY_TO_DIR = {
        'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)
    }

    if PLAYER.creature.move(KEY_TO_DIR[key][0], KEY_TO_DIR[key][1], game_vars.level.current_map):
        CAMERA.move(KEY_TO_DIR[key][0], KEY_TO_DIR[key][1])
        game_vars.fov_recompute = True

    return "player-moved"

def game_player_turn_input(key):
    if key == blt.TK_UP:
        return game_key_move('UP')
    if key == blt.TK_DOWN:
        return game_key_move('DOWN')
    if key == blt.TK_LEFT:
        return game_key_move('LEFT')
    if key == blt.TK_RIGHT:
        return game_key_move('RIGHT')

    if key == blt.TK_PERIOD and blt.check(blt.TK_SHIFT):
        if game_vars.level.current_map[PLAYER.x][PLAYER.y] == get_index(TileTypes.STAIRS):  # .stairs:
            GAME.next_level()

    if key == blt.TK_COMMA and blt.check(blt.TK_SHIFT):
        if game_vars.level.current_map[PLAYER.x][PLAYER.y] == get_index(TileTypes.STAIRS_UP):
            GAME.previous_level(game_vars.level.gen_type)

    # items
    if key == blt.TK_G:
        ents = map_check_for_items(PLAYER.x, PLAYER.y, game_vars.level.current_entities)
        if ents is not None:
            if len(ents) > 1:
                chosen_item = gui_menus.pickup_menu(ents)
                if chosen_item is not None:
                    chosen_item.item.pick_up(PLAYER)
                    return "player-moved"
            else:
                ents[0].item.pick_up(PLAYER)
                return "player-moved"

    if key == blt.TK_D:
        chosen_item = gui_menus.drop_menu(PLAYER)
        if chosen_item is not None:
            PLAYER.container.inventory[chosen_item].item.drop(PLAYER)
            return "player-moved"

    if key == blt.TK_I:
        chosen_item = gui_menus.inventory_menu("Inventory", PLAYER)
        if chosen_item is not None:
            if chosen_item.item:
                action = gui_menus.item_actions_menu(chosen_item)
                if action is None:
                    return
                # actions
                if action == 0:
                    chosen_item.item.use(PLAYER)
                elif action == 1:
                    chosen_item.item.drop(PLAYER)
                    return "player-moved"

    if key == blt.TK_C:
        gui_menus.character_sheet_menu("Character sheet", PLAYER)

    if key == blt.TK_R:
        PLAYER.creature.player.rest_start(30)
        return "player-moved"

    if key == blt.TK_E:
        # toggle
        if not PLAYER.creature.player.autoexplore:
            PLAYER.creature.player.autoexplore = True
        else:
            PLAYER.creature.player.autoexplore = False

        if PLAYER.creature.player.autoexplore:
            x,y = find_unexplored_closest(PLAYER.x, PLAYER.y, game_vars.level.current_map, game_vars.level.current_explored)
            print("Closest unexplored is " + str(x) + " " + str(y))
            moved = PLAYER.creature.player.move_towards_autoexplore(x, y, game_vars.level.current_map)
            if (moved[0]):
                CAMERA.move(moved[1], moved[2])
                game_vars.fov_recompute = True

            return "player-moved"


def game_handle_keys():
    key = blt.read()
    if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
        return "QUIT"

    if game_vars.game_state == GameStates.MAIN_MENU:
        if key not in (blt.TK_S, blt.TK_L):
            return "QUIT"

    if key == blt.TK_L:
        gui_menus.log_menu("Log history", 0, 26)

    if key == blt.TK_SLASH and blt.check(blt.TK_SHIFT):
        gui_menus.help_menu()

    # Debugging
    if key == blt.TK_GRAVE and blt.check(blt.TK_SHIFT):
        # print("Debug mode on")
        # constants.DEBUG = True
        gui_menus.debug_menu(PLAYER)


    #print("Mouse: " + str(game_handle_mouse_input(key)))
    game_handle_mouse_input(key)

    if game_vars.game_state == GameStates.PLAYER_TURN:
        #print (game_player_turn_input(key))
        return game_player_turn_input(key)


    return "no-action"