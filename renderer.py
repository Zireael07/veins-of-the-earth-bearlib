# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod


import constants

# based on STI library for LOVE2D
def draw_iso(x,y):
    # isometric
    offset_x = constants.MAP_WIDTH * 4
    tile_x = (x - y) * constants.TILE_WIDTH / 2 + offset_x
    tile_y = (x + y) * constants.TILE_HEIGHT / 2
    return tile_x, tile_y

def draw_map(map_draw, fov_map):
    for x in range(0, constants.MAP_WIDTH):
        for y in range(0, constants.MAP_HEIGHT):

            is_visible = libtcod.map_is_in_fov(fov_map, x, y)

            if is_visible:
                blt.color("white")
                map_draw[x][y].explored = True
                # cartesian
                # tile_x = x*constants.TILE_WIDTH
                # tile_y = y*constants.TILE_HEIGHT

                tile_x, tile_y = draw_iso(x,y)

                if map_draw[x][y].block_path == True:
                    # draw wall
                    blt.put(tile_x, tile_y, "#")

                else:
                    # draw floor
                    blt.put(tile_x, tile_y, 0x3002)

                    blt.put(tile_x,tile_y, ".")



            elif map_draw[x][y].explored:
                blt.color("gray")
                # cartesian
                # tile_x = x * constants.TILE_WIDTH
                # tile_y = y * constants.TILE_HEIGHT

                tile_x, tile_y = draw_iso(x,y)

                if map_draw[x][y].block_path == True:
                    # draw wall
                    blt.put(tile_x,tile_y, "#")
                else:
                    # draw floor
                    blt.put(tile_x, tile_y, 0x3002)
                    blt.put(tile_x,tile_y, ".")



def draw_messages(msg_history):
    if len(msg_history) <= constants.NUM_MESSAGES:
        to_draw = msg_history
    else:
        to_draw = msg_history[-constants.NUM_MESSAGES:]

    start_y = 45 - (constants.NUM_MESSAGES)

    i = 0
    for message, color in to_draw:
        string = "[color=" + str(color) + "] " + message
        blt.puts(2, start_y+i, string)

        i += 1


# GUI
# based on https://github.com/FirstAidKitten/Roguelike-Sandbox
def create_window(x, y, w, h, title=None):
    #test
    blt.composition(False)

    last_bg = blt.state(blt.TK_BKCOLOR)
    blt.bkcolor(blt.color_from_argb(200, 0, 0, 0))
    blt.clear_area(x - 2, y - 2, w + 2, h + 2)
    blt.bkcolor(last_bg)

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


def menu(header, options, width, title=None):
    global FOV_CALCULATE

    FOV_CALCULATE = True

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


def inventory_menu(header, player):
    # show a menu with each item of the inventory as an option
    if len(player.container.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.display_name() for item in player.container.inventory]

    index = menu(header, options, 50, 'INVENTORY')

    # if an item was chosen, return it
    if index is None or len(player.container.inventory) == 0:
        return None
    return player.container.inventory[index]

def character_sheet_menu(header, player):
    options = ["STR: " + str(player.creature.strength), "DEX: " + str(player.creature.dexterity), "CON: " + str(player.creature.constitution),
               "INT: " + str(player.creature.intelligence), "WIS: " + str(player.creature.wisdom), "CHA: " + str(player.creature.charisma)]

    index = menu(header, options, 50, 'CHARACTER SHEET')

    if index is None:
        return None

