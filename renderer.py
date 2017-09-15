# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod

import time

from map_common import tile_types

import constants

def initialize_camera(camera):
    global CAMERA
    CAMERA = camera

def initialize_game(game):
    global GAME
    GAME = game

# based on STI library for LOVE2D
def draw_iso(x,y):
    # isometric
    offset_x = constants.MAP_WIDTH * 4
    tile_x = (x - y) * constants.TILE_WIDTH / 2 + offset_x
    tile_y = (x + y) * constants.TILE_HEIGHT / 2
    return tile_x + CAMERA.offset[0], tile_y + CAMERA.offset[1]

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


def draw_map(map_draw, map_explored, fov_map):
    width = constants.MAP_WIDTH
    height = constants.MAP_HEIGHT
    debug = constants.DEBUG

    for x in range(0, width):
        for y in range(0, height):
            #tile_x, tile_y = draw_iso(x, y)
            is_in_map_range = CAMERA.rectangle.contains((x,y))  #((tile_x,tile_y))
            #print("Is in map range " + str(tile_x) + " " + str(tile_y) + ": " + str(is_in_map_range))

            if is_in_map_range:
                if debug:
                    is_visible = True
                else:
                    is_visible = libtcod.map_is_in_fov(fov_map, x, y)

                if is_visible:
                    #blt.color("white")
                    blt.color(4294967295)

                    map_explored[x][y] = True
                    #map_draw[x][y].explored = True

                    # cartesian
                    # tile_x = x*constants.TILE_WIDTH
                    # tile_y = y*constants.TILE_HEIGHT

                    tile_x, tile_y = draw_iso(x,y)

                    blt.put(tile_x, tile_y, tile_types[map_draw[x][y]].tile_put)


                elif map_explored[x][y]: #map_draw[x][y].explored:
                    #blt.color("gray")
                    blt.color(4286545791)
                    # cartesian
                    # tile_x = x * constants.TILE_WIDTH
                    # tile_y = y * constants.TILE_HEIGHT

                    tile_x, tile_y = draw_iso(x,y)

                    blt.put(tile_x, tile_y, tile_types[map_draw[x][y]].tile_put)


def draw_mouseover(x,y):
    tile_x, tile_y = pix_to_iso(x, y)
    draw_x, draw_y = draw_iso(tile_x, tile_y)

    blt.color("light yellow")
    blt.put(draw_x, draw_y, 0x2317)


def draw_messages(msg_history):
    if len(msg_history) <= constants.NUM_MESSAGES:
        to_draw = msg_history
    else:
        to_draw = msg_history[-constants.NUM_MESSAGES:]

    start_y = blt.state(blt.TK_HEIGHT) - (constants.NUM_MESSAGES)

    i = 0
    for message, color in to_draw:
        string = "[color=" + str(color) + "] " + message
        blt.puts(2, start_y+i, string)

        i += 1

def draw_bar(x, y, total_width, name, value, maximum, bar_color, bg_color, label=None):

    blt.puts(x, y-1, name)

    bar_width = int(float(value) / maximum * total_width)

    for i in range(total_width):
        blt.color(bg_color)
        if i < bar_width:
            blt.color(bar_color)
        blt.put(x + i, y, 0x2588)

    if label:
        blt.color("white")
        blt.puts(x+int(total_width/2), y, label)

# GUI
# based on https://github.com/FirstAidKitten/Roguelike-Sandbox
def create_window(x, y, w, h, title=None, border=True):
    #test
    blt.composition(False)

    last_bg = blt.state(blt.TK_BKCOLOR)
    blt.bkcolor(blt.color_from_argb(200, 0, 0, 0))
    blt.clear_area(x - 2, y - 2, w + 2, h + 2)
    blt.bkcolor(last_bg)

    if border:
        # upper border
        border = '┌' + '─' * (w) + '┐'
        blt.puts(x - 1, y - 1, border)
        # sides
        for i in range(h):
            blt.puts(x - 1, y + i, '│')
            blt.puts(x + w, y + i, '│')
        # lower border
        border = '└' + '─' * (w) + '┘'
        blt.puts(x - 1, y + h, border)

    if title is not None:
        leng = len(title)
        offset = (w + 2 - leng) // 2
        blt.puts(x + offset, y - 1, title)


def options_menu(header, options, width, title=None):
    GAME.fov_recompute = True

    menu_x = int((120 - width) / 2)

    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    header_height = 2

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)

    # create a window

    create_window(menu_x, menu_y, width, menu_h, title)


    blt.puts(menu_x, menu_y, header)

    # print all the options
    y = menu_y + header_height + 1
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        blt.puts(menu_x, y, text)
        y += 1
        letter_index += 1

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()
        if blt.check(blt.TK_CHAR):
            # convert the ASCII code to an index; if it corresponds to an option, return it
            key = blt.state(blt.TK_CHAR)
            index = key - ord('a')
            if 0 <= index < len(options):
                blt.set('input: filter = [keyboard, mouse+]')
                blt.composition(True)
                return index
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return None

# this one doesn't show keys and conversely doesn't have the 26 entries limit
# it takes tuples instead of strings
def menu_colored(header, options_tuples, width, title=None, menu_x=None, border=True):
    GAME.fov_recompute = True

    if menu_x is None:
        menu_x = int((120 - width) / 2)

    header_height = 2

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)

    # create a window

    create_window(menu_x, menu_y, width, menu_h, title, border)

    blt.puts(menu_x, menu_y, header)

    # print all the options
    y = menu_y + header_height + 1
    for option in options_tuples:
        string = "[color=" + str(option[1]) + "] " + option[0]

        blt.puts(menu_x, y, string)
        y += 1

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()
        blt.set('input: filter = [keyboard, mouse+]')
        blt.composition(True)
        return key

# scrolling version of the above
def menu_colored_scrolled(header, options_tuples, width, begin, end, title=None):
    GAME.fov_recompute = True

    menu_x = int((120 - width) / 2)

    header_height = 2

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)

    # calculate
    if len(options_tuples) - 1 <= end:
        end = len(options_tuples) - 1

    # create a window
    create_window(menu_x, menu_y, width, menu_h, title)

    blt.puts(menu_x, menu_y, header)

    # print all the options
    y = menu_y + header_height + 1
    # for option in options_tuples:
    for i in range(begin, end):
        option = options_tuples[i]
        string = "[color=" + str(option[1]) + "] " + option[0]

        blt.puts(menu_x, y, string)
        y += 1

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()

        if key == blt.TK_UP:
            #print("Pressed up key in scrolling menu")
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return -1, begin, end

        if key == blt.TK_DOWN:
            #print("Pressed down key in scrolling menu")

            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return 1, begin, end

        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return None, begin, end

# individual menus

def inventory_menu(header, player):
    # show a menu with each item of the inventory as an option
    if len(player.container.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.display_name() for item in player.container.inventory]

    index = options_menu(header, options, 50, 'INVENTORY')

    # if an item was chosen, return it
    if index is None or len(player.container.inventory) == 0:
        return None
    return player.container.inventory[index]

def character_sheet_menu(header, player):
    options = [("STR: " + str(player.creature.strength), "white"), ("DEX: " + str(player.creature.dexterity), "white"),
               ("CON: " + str(player.creature.constitution), "white"), ("INT: " + str(player.creature.intelligence), "white"),
                ("WIS: " + str(player.creature.wisdom), "white"), ("CHA: " + str(player.creature.charisma), "white"),
               ("Attack: " + str(player.creature.melee), "white"), ("Dodge: " + str(player.creature.dodge), "white")

               ]

    index = menu_colored(header, options, 50, 'CHARACTER SHEET')

    if index is None:
        return None


def log_menu(header, begin, end):
    options = GAME.message_history

    scroll = menu_colored_scrolled(header, options, 50, begin, end, 'LOG HISTORY')

    if scroll is not None:
        return scroll

def dmg_menu(header):
    options = ["Damage display"]
    index = options_menu(header, options, 30)

    if index is None:
        return None


def display_dmg_window(index):
    if "damage" in GAME.message_history[index][0]:
        #print("The line says damage!")

        # extract the dmg number
        dmg = filter(str.isdigit, str(GAME.message_history[index][0]))
        dmg_menu(dmg)

def main_menu():

    key = menu_colored("MAIN MENU", [("(S)tart new game", "white"), ("(L)oad game", "white"), ("(E)xit game", "white")],
                       50, menu_x = int((180 - 50) / 2), border=False)

    if key == blt.TK_S:
        return 1
    if key == blt.TK_L:
        return 2

# drawing special effects
def wait(wait_time):
    wait_time = wait_time * 0.01
    start_time = time.time()


    while time.time() - start_time < wait_time:
        blt.refresh()

def draw_effect(x,y, tile, speed, clear, color="white"):
    blt.color(color)
    blt.put_ext(x, y, 0, 0, tile)
    wait(8*speed)
    if clear:
        blt.clear_area(x,y)

def draw_effects(effects, speed, clr_x, clr_y, clr_w=1, clr_h=1):
    for eff in effects:
        draw_effect(eff[1],eff[2], eff[0], speed, False, eff[3])

    blt.clear_area(clr_x,clr_y, clr_w, clr_h)

def draw_blood_splatter(x,y, damage):
    effects = []
    effects.append((0x2BC1, x, y, "red"))
    w = 1
    for l in str(damage):
        effects.append((l, x, y, "white"))
        x + 1
        w += 1

    draw_effects(effects, 1.5, x, y, w,1)

def draw_shield(x,y):
    draw_effect(x,y, 0x2BC2, 1.5, True)