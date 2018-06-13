from bearlibterminal import terminal as blt

import gui_menus
import os
import game_loaders

from map_common import map_make_fov, map_check_for_creature, find_free_grid_in_range

import hud
import handle_input

import game_vars

import camera
import game

import generators
import components
import events
from game_states import GameStates

def death_player(player):
    events.notify(events.GameEvent("MESSAGE", (player.creature.name_instance + " is dead!", "dark red")))
    # remove from map
    game_vars.level.current_entities.remove(player)
    # show death screen
    kid = gui_menus.death_menu(player)
    if kid:
        #and kid in game_vars.level.current_entities:
        print("Should be switching control to kid!!!")
        player.creature.player.switch_to_kid(kid)
    else:
        # set game state to player dead
        game_vars.game_state = GameStates.PLAYER_DEAD
        #delete savegame (this assumes we can only have one)
        if os.path.isfile('savegame.json'):
            os.remove('savegame.json')

def generate_player():
    container_com1 = components.com_Container()
    player_array = generators.generate_stats("heroic")

    player_com1 = components.com_Player()
    creature_com1 = components.com_Creature("Player", hp=20,
                                            base_str=player_array[0], base_dex=player_array[1],
                                            base_con=player_array[2],
                                            base_int=player_array[3], base_wis=player_array[4],
                                            base_cha=player_array[5],
                                            languages=[ u"Common"],
                                            player=player_com1, faction="player", death_function=death_player)

    # body parts
    creature_com1.set_body_parts(generators.generate_body_types())

    # check that x,y isn't taken
    x, y = game_vars.level.player_start_x, game_vars.level.player_start_y
    taken = map_check_for_creature(x, y)
    if taken is not None:
        print("Looking for grid in range")
        grids = find_free_grid_in_range(3, x, y)
        # grids = find_grid_in_range(3, x,y)
        if grids is not None:
            x, y = grids[0]
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
    cam = camera.obj_Camera()
    # init camera for renderer
    #renderer.initialize_camera(cam)
    game_vars.camera = cam

    game_obj = game.obj_Game(False, seed)

    # init factions
    game_obj.add_faction(("player", "enemy", -100))
    game_obj.add_faction(("player", "neutral", 0))

    # spawn player
    player = generate_player()

    # adjust camera position so that player is centered
    cam.start_update(player)

    game_vars.game_obj = game_obj

    # put player last
    game_vars.player = player
    game_vars.level.current_entities.append(player)

    # test
    generators.get_random_item()

    return game_obj, player, cam


def main_menu_outer():
    ret = main_menu()
    while ret is False:
        ret = main_menu()

    return ret

def main_menu():
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
        #hud.initialize_player(PLAYER)

        # handle input needs player
        #handle_input.initialize_player(PLAYER)

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