from bearlibterminal import terminal as blt

import gui_menus
import os
import game_loaders

from map_common import map_make_fov

import components
import generators
import level
import renderer
import hud
import handle_input

import game_vars




def main_menu(start_new_game):
    blt.put(10, 0, 0xE100)
    action = gui_menus.main_menu()

    # if we have a savegame, load it
    if action == 2 and os.path.isfile('savegame.json'):
        GAME, PLAYER, CAMERA = game_loaders.load_game()

        # handle FOV
        game_vars.fov_recompute = True
        # recreate the fov
        game_vars.fov_map = map_make_fov(game_vars.level.current_map)
        game_vars.ai_fov_map = map_make_fov(game_vars.level.current_map)

        # patch in required stuff
        # init game for submodules
        components.initialize_game(GAME)
        generators.initialize_game(GAME)
        #level.initialize_game(GAME)
        #renderer.initialize_game(GAME)
        #gui_menus.initialize_game(GAME)

        # init camera for renderer
        renderer.initialize_camera(CAMERA)

        #hud.initialize_game(GAME)
        hud.initialize_player(PLAYER)

        # handle input needs all three
        handle_input.initialize_game(GAME)
        handle_input.initialize_player(PLAYER)
        handle_input.initialize_camera(CAMERA)

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

    else:
        return None