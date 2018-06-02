from bearlibterminal import terminal as blt

import constants
from game_states import GameStates
import gui_menus
from renderer import pix_to_iso
from map_common import map_check_for_items, find_unexplored_closest, Directions, find_exit_for_pos
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

            if click_x >= 0 and click_x < len(game_vars.level.current_map):
                if click_y >= 0 and click_y < len(game_vars.level.current_map[0]):
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

# these directions mean that up goes up on the displayed map
KEY_TO_DIR = {
        blt.TK_UP: Directions.NORTHWEST, blt.TK_DOWN: Directions.SOUTHEAST,
        blt.TK_LEFT: Directions.SOUTHWEST, blt.TK_RIGHT: Directions.NORTHEAST,
        blt.TK_HOME: Directions.WEST, blt.TK_PAGEUP: Directions.NORTH,
        blt.TK_PAGEDOWN: Directions.SOUTH, blt.TK_END: Directions.EAST,
    # numpad
        blt.TK_KP_8: Directions.NORTHWEST, blt.TK_KP_2: Directions.SOUTHEAST,
        blt.TK_KP_4: Directions.SOUTHWEST, blt.TK_KP_6: Directions.NORTHEAST,
        blt.TK_KP_7: Directions.WEST, blt.TK_KP_9: Directions.NORTH,
        blt.TK_KP_1: Directions.SOUTH, blt.TK_KP_3: Directions.EAST
    }

KEY_TO_DIR_VI = {
        blt.TK_K: Directions.NORTHWEST, blt.TK_J: Directions.SOUTHEAST,
        blt.TK_H: Directions.SOUTHWEST, blt.TK_L: Directions.NORTHEAST,
        blt.TK_Y: Directions.WEST, blt.TK_U: Directions.NORTH,
        blt.TK_B: Directions.SOUTH, blt.TK_N: Directions.EAST
}

def get_up_key():
    # no way to convert the integer back to string...
    #src = KEY_TO_DIR if not constants.VI_KEYS else KEY_TO_DIR_VI
    #return str(src.keys()[0])

    if constants.VI_KEYS:
        return "K"
    else:
        return "UP/KP 8"

def game_key_move(key):
    src = KEY_TO_DIR if not constants.VI_KEYS else KEY_TO_DIR_VI
    if PLAYER.creature.move(src[key][0], src[key][1], game_vars.level.current_map):
        CAMERA.move(src[key][0], src[key][1])
        game_vars.fov_recompute = True

        # clear move queue
        PLAYER.creature.move_queue = []
        # switch off a-e
        PLAYER.creature.player.autoexplore = False

    return "player-moved"

def game_player_turn_input(key):
    if not constants.VI_KEYS and key in KEY_TO_DIR or constants.VI_KEYS and key in KEY_TO_DIR_VI:
        return game_key_move(key)

    if blt.check(blt.TK_SHIFT) and key == blt.TK_PERIOD:
        if game_vars.level.current_map[PLAYER.x][PLAYER.y] == get_index(TileTypes.STAIRS):  # .stairs:
            if hasattr(game_vars.level, 'exits'):
                dest = find_exit_for_pos(PLAYER.x, PLAYER.y)

                GAME.next_level(dest)
            else:
                GAME.next_level()
            return "redraw"
            #return "player-moved"

    if blt.check(blt.TK_SHIFT) and key == blt.TK_COMMA:
        if game_vars.level.current_map[PLAYER.x][PLAYER.y] == get_index(TileTypes.STAIRS_UP):
            GAME.previous_level(game_vars.level.gen_type)
            return "redraw"
            #return "player-moved"

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
                    return "player-moved"
                elif action == 1:
                    chosen_item.item.drop(PLAYER)
                    return "player-moved"

    if key == blt.TK_C:
        gui_menus.character_sheet_menu("Character sheet", PLAYER)

    if key == blt.TK_R:
        PLAYER.creature.player.rest_start(30)
        return "player-moved"

    # # testing
    # if key == blt.TK_M:
    #     if PLAYER.creature.player.autoexplore:
    #
    #         # do we have a queue?
    #         if len(PLAYER.creature.player.move_queue) > 1:
    #             print("We have a queue")
    #             moved = PLAYER.creature.player.moves_from_queue()
    #
    #             if (moved[0]):
    #                 CAMERA.move(moved[1], moved[2])
    #                 game_vars.fov_recompute = True
    #
    #             return "player-moved"
    #
    #         else:
    #             print("No queue!")
    #     else:
    #         print("Not autoexploring")

    if key == blt.TK_E:
        # toggle
        if not PLAYER.creature.player.autoexplore:
            PLAYER.creature.player.autoexplore = True
        else:
            PLAYER.creature.player.autoexplore = False

        if PLAYER.creature.player.autoexplore:

            # do we have a queue?
            if len(PLAYER.creature.move_queue) > 1:
                print("We have a queue")
                moved = PLAYER.creature.moves_from_queue()

            else:
                x, y = find_unexplored_closest(PLAYER.x, PLAYER.y, game_vars.level.current_map,
                                               game_vars.level.current_explored)
                print("Closest unexplored is " + str(x) + " " + str(y))
                PLAYER.creature.move_towards_path_queue(x, y, game_vars.level.current_map)

                moved = PLAYER.creature.moves_from_queue()

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

    if not constants.VI_KEYS and key == blt.TK_L or constants.VI_KEYS and blt.check(blt.TK_SHIFT) and key == blt.TK_M:
        gui_menus.log_menu("Log history", 0, 26)

    if blt.check(blt.TK_SHIFT) and key == blt.TK_SLASH:
        gui_menus.help_menu()

    # Debugging
    if blt.check(blt.TK_SHIFT) and key == blt.TK_GRAVE:
        # print("Debug mode on")
        # constants.DEBUG = True
        return gui_menus.debug_menu(PLAYER)

    # Toggle labels
    if key == blt.TK_TAB:
        #print("Toggle labels")
        game_vars.labels = not game_vars.labels
        print("Labels: " + " " + str(game_vars.labels))
        blt.layer(4)
        blt.clear_area(0, 0, blt.state(blt.TK_WIDTH, blt.state(blt.TK_HEIGHT)))
        if game_vars.labels:
            return "redraw"

    if key == blt.TK_MOUSE_LEFT or key == blt.TK_MOUSE_RIGHT:
        #print("Mouse input")
        return game_handle_mouse_input(key)

    if game_vars.game_state == GameStates.PLAYER_TURN:
        #print (game_player_turn_input(key))
        return game_player_turn_input(key)


    return "no-action"