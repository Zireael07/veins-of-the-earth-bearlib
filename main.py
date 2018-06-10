#!/usr/bin/python2
# coding: utf8

from bearlibterminal import terminal as blt
#import libtcodpy as libtcod
from time import time

import game
# save/load
import game_loaders

import constants
import tileset
import renderer

import hud

import main_menu
import game_vars

import handle_input
from game_states import GameStates


def cell_to_iso(x,y):
    offset_x = constants.MAP_WIDTH * 4
    iso_x = y / constants.TILE_HEIGHT + (x - offset_x) / constants.TILE_WIDTH
    iso_y = y / constants.TILE_HEIGHT - (x - offset_x) / constants.TILE_WIDTH - CAMERA.offset[1]
    return iso_x, iso_y


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

            # debug
            blt.puts(2,2, "Redraw: %s" % str(game_vars.redraw))

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
                renderer.draw_game()


            # on top of map
            blt.layer(1)
            renderer.draw_messages(game_vars.message_history)

            blt.layer(1)
            renderer.draw_mouseover(pix_x, pix_y)
            blt.color(4294967295)

            hud.draw_hud(pix_x, pix_y)

            # effects
            for ef in game_vars.level.current_effects:
                ef.update()
                if not ef.render:
                     game_vars.level.current_effects.remove(ef)

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
            if handle_input.get_fake_action() is not None:
                print("Faking an action")
                player_action = handle_input.get_fake_action()
                handle_input.reset_fake_action()
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
                # force redraw
                game_vars.redraw = True
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
        3, 7,
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
    GAME = game.obj_Game(True)
    game_vars.game_state = GameStates.MAIN_MENU

    ret = main_menu.main_menu_outer()
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


