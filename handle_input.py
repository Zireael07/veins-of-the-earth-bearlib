from bearlibterminal import terminal as blt

import constants
from game_states import GameStates
import renderer
from map_common import map_check_for_item

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

    if not GAME.message_history:
        return None

    if len(GAME.message_history) < 4:
        check = -len(GAME.message_history)


    if GAME.message_history[check]:
        return check


def click_on_msg_log(m_y):
    log_h = blt.state(blt.TK_HEIGHT) - (constants.NUM_MESSAGES)
    # which line?
    if m_y == log_h:
        # print("Clicked over line #1")
        check = get_top_log_string_index()
        if check is not None:
            print(GAME.message_history[check])
            renderer.display_dmg_window(check)

    elif m_y == log_h + 1:
        check = get_top_log_string_index()
        if check is not None:
            print(GAME.message_history[check + 1])
            renderer.display_dmg_window(check + 1)

    elif m_y == log_h + 2:
        check = get_top_log_string_index()
        if check is not None:
            print(GAME.message_history[check + 2])
            renderer.display_dmg_window(check + 2)
    elif m_y == log_h + 3:
        check = get_top_log_string_index()
        if check is not None:
            print(GAME.message_history[check + 3])
            renderer.display_dmg_window(check + 3)


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

            click_x, click_y = renderer.pix_to_iso(pix_x, pix_y)

            if click_x > 0 and click_x < constants.MAP_WIDTH - 1:
                if click_y > 0 and click_y < constants.MAP_HEIGHT - 1:
                    print "Clicked on tile " + str(click_x) + " " + str(click_y)

                    if click_x != PLAYER.x or click_y != PLAYER.y:
                        moved = PLAYER.creature.move_towards(click_x, click_y, GAME.current_map)
                        if (moved[0]):
                            CAMERA.move(moved[1], moved[2])
                            GAME.fov_recompute = True

                    return "player-moved"

    # pressed right mouse button
    if key == blt.TK_MOUSE_RIGHT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)
        print "Right clicked on tile " + str(renderer.pix_to_iso(pix_x, pix_y))

        return "mouse_click"

def game_key_move(key):
    KEY_TO_DIR = {
        'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)
    }

    if PLAYER.creature.move(KEY_TO_DIR[key][0], KEY_TO_DIR[key][1], GAME.current_map):
        CAMERA.move(KEY_TO_DIR[key][0], KEY_TO_DIR[key][1])
        GAME.fov_recompute = True

    return "player-moved"


def game_handle_keys():
    key = blt.read()
    if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
        return "QUIT"

    if GAME.game_state == GameStates.PLAYER_TURN:
        if key == blt.TK_UP:
            return game_key_move('UP')
        if key == blt.TK_DOWN:
            return game_key_move('DOWN')
        if key == blt.TK_LEFT:
            return game_key_move('LEFT')
        if key == blt.TK_RIGHT:
            return game_key_move('RIGHT')

        # items
        if key == blt.TK_G:
            ent = map_check_for_item(PLAYER.x, PLAYER.y, GAME)
            #for ent in objects:
            ent.item.pick_up(PLAYER)

        if key == blt.TK_D:
            if len(PLAYER.container.inventory) > 0:
                #drop the last item
                PLAYER.container.inventory[-1].item.drop(PLAYER)

        if key == blt.TK_I:
            chosen_item = renderer.inventory_menu("Inventory", PLAYER)
            if chosen_item is not None:
                if chosen_item.item:
                    chosen_item.item.use(PLAYER)

        if key == blt.TK_C:
            renderer.character_sheet_menu("Character sheet", PLAYER)

    if key == blt.TK_L:
        renderer.log_menu("Log history")

    if key == blt.TK_GRAVE and blt.check(blt.TK_SHIFT):
        print("Debug mode on")
        constants.DEBUG = True

    game_handle_mouse_input(key)


    return "no-action"