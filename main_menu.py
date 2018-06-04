from bearlibterminal import terminal as blt

import gui_menus
import os
import game_loaders

from map_common import map_make_fov

import components
import renderer
import hud
import handle_input

import game_vars


def main_menu_outer(start_new_game):
    ret = main_menu(start_new_game)
    while ret is False:
        ret = main_menu(start_new_game)

    return ret

def main_menu(start_new_game):
    blt.put(10, 0, 0xE100)
    action = gui_menus.main_menu()

    # if we have a savegame, load it
    if action == 2 and os.path.isfile('savegame.json'):
        GAME, PLAYER, CAMERA = game_loaders.load_game()

        # handle FOV
        game_vars.fov_recompute = True
        # recreate the fov
        game_vars.fov_map = map_make_fov(game_vars.level.current_map, False)
        game_vars.ai_fov_map = map_make_fov(game_vars.level.current_map, True)

        # patch in required stuff
        hud.initialize_player(PLAYER)

        # handle input needs player
        handle_input.initialize_player(PLAYER)

        # we don't have to reset camera position because it's loaded from the file
        # CAMERA.start_update(PLAYER)

        print("Game loaded")

        GAME.set_player_turn()

        return GAME, PLAYER, CAMERA

    elif action == 1:
        # seed input
        blt.clear()
        seed = gui_menus.seed_input_menu()
        # print("Seed: "+ str(seed))

        GAME, PLAYER, CAMERA = start_new_game(seed)
        game_vars.fov_recompute = True

        GAME.set_player_turn()

        # show character creation
        blt.clear()
        gui_menus.character_creation_menu(PLAYER)

        return GAME, PLAYER, CAMERA

    elif action == 3:
        # options
        #blt.layer(4)
        option = gui_menus.options_menu_outer()
        #print("Option: " + str(option))
        if not option:
            print("Not option, going back")
            #blt.clear()
            return False

    else: #quit
        return None