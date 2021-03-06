# coding: utf8
from bearlibterminal import terminal as blt

import game_vars
from equipment_slots import EquipmentSlots

# GUI

# basic
def draw_box(x,y,w,h):
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


# based on https://github.com/FirstAidKitten/Roguelike-Sandbox
def create_window(x, y, w, h, title=None, border=True, layer=3):
    # test
    blt.composition(True)

    blt.layer(layer)
    #blt.layer(1)

    # fill the background
    blt.color("black")
    for i in range(w):
        for j in range(h):
            blt.put(x + i, y + j, 0x2588)

    # last_bg = blt.state(blt.TK_BKCOLOR)
    # blt.bkcolor(blt.color_from_argb(200, 0, 0, 0))
    # blt.clear_area(x - 2, y - 2, w + 2, h + 2)
    # blt.bkcolor(last_bg)

    blt.color("white")

    # otherwise border overlaps header text
    blt.composition(False)
    if border:
        draw_box(x,y,w,h)

    if title is not None:
        leng = len(title)
        offset = (w + 2 - leng) // 2
        blt.puts(x + offset, y - 1, title)

    blt.composition(True)

def setup_window(header_height, width, title):
    #GAME.fov_recompute = True
    menu_x = int((120 - width) / 2)

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)

    # create a window

    create_window(menu_x, menu_y, width, menu_h, title)

    return menu_x, menu_y, menu_h

def options_menu(header, options, width, title=None, layer=3):
    #GAME.fov_recompute = True

    menu_x = int((120 - width) / 2)

    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    header_height = 2

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)
    # offset for menus on further layers
    if layer > 3:
        menu_y = menu_y + layer

    # create a window
    create_window(menu_x, menu_y, width, menu_h, title, True, layer)


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
    blt.set('input: filter = [keyboard, mouse-left]')
    while True:
        key = blt.read()

        if key == blt.TK_MOUSE_LEFT:
            print("Pressed left mouse key")
            m_x = blt.state(blt.TK_MOUSE_X)
            m_y = blt.state(blt.TK_MOUSE_Y)

            click_x, click_y = (m_x - menu_x, m_y - menu_y - header_height - 1)
            # did we click in the menu
            if click_x >= 0 and click_x <= width and click_y >= 0 and click_y < menu_h - header_height - 1:
                print("Clicked, returning " + str(click_y))
                blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                return click_y

        if blt.check(blt.TK_CHAR):
            # convert the ASCII code to an index; if it corresponds to an option, return it
            key = blt.state(blt.TK_CHAR)
            index = key - ord('a')
            if 0 <= index < len(options):
                blt.set('input: filter = [keyboard, mouse+]')
                blt.composition(True)
                blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                return index
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
            return None

# this one doesn't show keys and conversely doesn't have the 26 entries limit
# it takes tuples instead of strings
def menu_colored(header, options_tuples, width, title=None, menu_x=None, border=True):
    #GAME.fov_recompute = True

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
    blt.set('input: filter = [keyboard, mouse-left]')
    while True:
        key = blt.read()

        if key == blt.TK_MOUSE_LEFT:
            print("Pressed left mouse key")
            m_x = blt.state(blt.TK_MOUSE_X)
            m_y = blt.state(blt.TK_MOUSE_Y)

            click_x, click_y = (m_x - menu_x, m_y - menu_y - header_height - 1)
            # did we click in the menu
            if click_x >= 0 and click_x <= width and click_y >= 0 and click_y < menu_h - header_height - 1:
                print("Clicked, returning " + str(click_y))
                blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                return click_y
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
            return key

# scrolling version of the above
def menu_colored_scrolled(header, options_tuples, width, begin, end, title=None):
    #GAME.fov_recompute = True

    menu_x = int((120 - width) / 2)

    header_height = 2

    menu_h = int(header_height + 1 + 27) #26 options plus one for the border
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
    for i in range(begin, end+1):
        option = options_tuples[i]
        string = "[color=" + str(option[1]) + "] " + option[0]

        blt.puts(menu_x, y, string)
        y += 1
	
    #scrollbar
    y = menu_y+header_height+1
    max_off = 26
    offset = (end/((len(game_vars.message_history)-1)*1.0))
    print("Offset: " + str(offset))
    blt.put(menu_x+width-1, y+int(offset*26), 0x2588)

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()

        if key == blt.TK_UP or key == blt.TK_K:
            print("Pressed up key in scrolling menu")
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return -1, begin, end

        if key == blt.TK_DOWN or key == blt.TK_J:
            print("Pressed down key in scrolling menu")

            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return 1, begin, end

        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            print("Pressed some other key in scrolling menu")  
            return None, begin, end


# used for character creation
def multicolumn_menu(title, columns, width, col_width, wanted_keys_num=1):
    current = 0
    ret = multicolumn_menu_inner(title, columns, width, col_width, current, None)
    if ret is not None:
        #print("Ret is not none " + str(ret))
        # if we are getting input, keep showing the window
        while ret is not None and len(ret[1]) < wanted_keys_num:
            #print("Ret is not none " + str(ret[1]))
            # column selection
            if ret[0] is not None:
                ret = multicolumn_menu_inner(title, columns, width, col_width, ret[0], ret[1])
            else:
                ret = multicolumn_menu_inner(title, columns, width, col_width, 0, ret[1])

        if ret is not None:
            print("Returning: " + str(ret) + ": " + str(ret[1]))
            return ret[1]

def multicolumn_menu_inner(title, columns, width, col_width, current, values):
    #GAME.fov_recompute = True

    menu_x = int((120 - width) / 2)

    if len(columns[0]) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    header_height = 2

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)

    # default column
    cur_column = current

    # create a window

    create_window(menu_x, menu_y, width, menu_h, title)

    blt.puts(menu_x, menu_y, "Press tab to change columns")

    # print all the options
    y = menu_y + header_height + 1
    # this continues the lettering between columns e.g ab | cd | ef
    letter_index = ord('a')

    if values is None:
        values = []

    x = menu_x
    for i in range(0, len(columns)):
        #col = columns[i]
        w = col_width
        y = menu_y + header_height + 2
        # outline current column
        if i == cur_column:
            h = len(columns[i])
            # upper border
            border = '┌' + '─' * (w) + '┐'
            blt.puts(x - 1, y - 1, border)
            # sides
            for j in range(h):
                blt.puts(x - 1, y + j, '│')
                blt.puts(x + w, y + j, '│')
            # lower border
            border = '└' + '─' * (w) + '┘'
            blt.puts(x - 1, y + h, border)


        # draw the column
        #letter_index = ord('a')
        for option_text in columns[i]:
            text = '(' + chr(letter_index) + ') ' + option_text
            blt.puts(x, y, text)
            y += 1
            letter_index += 1

        x += w+2

        i += 1

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()
        # change current column
        if key == blt.TK_TAB:
            if cur_column < len(columns)-1:
                return [cur_column+1, values]
            else:
                return [0, values]

        # handle options
        elif blt.check(blt.TK_CHAR):
            # convert the ASCII code to an index; if it corresponds to an option, return it
            key = blt.state(blt.TK_CHAR)
            index = key - ord('a')
            # this reacts to any of the keys listed in current column

            prev_column = None
            if cur_column > 0:
                prev_column = cur_column-1
                start = len(columns[prev_column])
            else:
                start = 0

            #print("Start " + str(start) + "end: " + str(start + len(columns[cur_column])))

            if start <= index < start + len(columns[cur_column]):
                blt.set('input: filter = [keyboard, mouse+]')
                blt.composition(True)
                blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                print("Pressed key " + str(index))

                if index not in values:
                    values.append(index)
                print(values)

                return [None, values]
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
            print("Pressed any key")
            return None




# inventory menu
def draw_slot(x,y,char=None):
    blt.layer(4)
    draw_box(x, y, 2, 1)
    if char is not None:
        blt.put_ext(x, y, 2, -1, char)

def quit_inventory_screen():
    blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
    blt.layer(4)
    blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
    blt.layer(5)
    blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
    # blt.layer(3)

def inventory_menu_test(header, width, title, equipped_items, inventory):
    header_height = 2
    menu_x, menu_y, _ = setup_window(header_height, width, title)

    blt.puts(menu_x, menu_y, header)

    y = menu_y + header_height + 1

    x = menu_x + 2

    letter_index = ord('a')

    # draw paperdoll
    blt.layer(4)
    blt.put(x, y, game_vars.player.char)

    for obj in game_vars.player.container.equipped_items:
        if hasattr(obj.item, 'paperdoll'):
            blt.put(x, y, obj.item.paperdoll)

    x = menu_x + 10
    #y = menu_y + 6

    # draw equipped items
    blt.layer(4)
    # reverse mapping of a custom enum is a dict that we can iterate on
    for index in range(1, len(EquipmentSlots.reverse_mapping)+1):
        slot = EquipmentSlots.reverse_mapping[index]

        name = str(slot).lower()

        # line change every three slots
        if index % 4 == 0:
            x = menu_x + 10
            y = y + 5


        # slot label
        blt.puts(x-1,y+2, name.capitalize())

        if len(equipped_items) > 0:
            for i in range (len(equipped_items)):
                item_eq = equipped_items[i]
                if item_eq.equipment.slot == name:
                    #print("Item " + str(item.name) + " index is " + str(inventory.index(item)))
                    char = item_eq.char
                    draw_slot(x, y, char)
                    # draw the inventory letter
                    text = '(' + chr(letter_index + inventory.index(item_eq)) + ') '
                    blt.puts(x-1, y - 2, text)
                else:
                    draw_slot(x,y, None)
        else:
            draw_slot(x,y, None)

        x = x + 10

    y = y + 3

    # back to 1st row
    x = menu_x + 2
    blt.puts(x, y, '─' * 40)

    y = y + 3

    # draw inventory slots (ignoring the items that are equipped)
    slots = [item for item in inventory if item.equipment and not item.equipment.equipped or not item.equipment]


    for i in range(0,10):
        if len(inventory) > 0:
            if len(slots) > i:
            #if len(inventory) > i:
                item = slots[i]
                #item = inventory[i]
                if not item.equipment or not item.equipment.equipped:
                    #print("Item " + str(item.name) + " index is " + str(inventory.index(item)))
                    char = item.char
                    draw_slot(x, y, char)
                    # draw the inventory letter
                    text = '(' + chr(letter_index + inventory.index(item)) + ') '
                    blt.puts(x - 1, y - 2, text)
                    #letter_index += 1
                else:
                    draw_slot(x,y, None)
            else:
                draw_slot(x,y,None)
        else:
            draw_slot(x,y,None)

        x = x + 4

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()
        if blt.check(blt.TK_CHAR):
            # convert the ASCII code to an index; if it corresponds to an option, return it
            key = blt.state(blt.TK_CHAR)
            index = key - ord('a')
            if 0 <= index < len(inventory):
                blt.set('input: filter = [keyboard, mouse+]')
                blt.composition(True)
                quit_inventory_screen()
                return index
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            quit_inventory_screen()
            return None

def dialogue_menu(header, width, title, text, answers):
    header_height = 2
    menu_x, menu_y, menu_h = setup_window(header_height, width, title)

    blt.puts(menu_x, menu_y, header)

    y = menu_y + header_height + 1

    blt.puts(menu_x, y, text)

    y = y + 2

    letter_index = ord('a')
    for answer in answers:
        answer_text = answer['chat']
        text = '(' + chr(letter_index) + ') ' + answer_text
        blt.puts(menu_x, y, text)
        y += 1
        letter_index += 1

    blt.refresh()
    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard, mouse-left]')
    while True:
        key = blt.read()

        if key == blt.TK_MOUSE_LEFT:
            print("Pressed left mouse key")
            m_x = blt.state(blt.TK_MOUSE_X)
            m_y = blt.state(blt.TK_MOUSE_Y)

            click_x, click_y = (m_x - menu_x, m_y - menu_y - header_height - 3)
            # did we click in the menu
            if click_x >= 0 and click_x <= width and click_y >= 0 and click_y < menu_h - header_height - 3:
                print("Clicked, returning " + str(click_y))
                blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                return click_y

        if blt.check(blt.TK_CHAR):
            # convert the ASCII code to an index; if it corresponds to an option, return it
            key = blt.state(blt.TK_CHAR)
            index = key - ord('a')
            if 0 <= index < len(answers):
                blt.set('input: filter = [keyboard, mouse+]')
                blt.composition(True)
                blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
                return index
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
            return None

def text_menu(header, width, title, text):
    header_height = 2
    menu_x, menu_y, _ = setup_window(header_height, width, title)

    blt.puts(menu_x, menu_y, header)

    y = menu_y + header_height + 1

    blt.puts(menu_x, y, text)

    blt.refresh()

    # present the root console to the player and wait for a key-press
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()
        blt.set('input: filter = [keyboard, mouse+]')
        blt.composition(True)
        blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
        return key

def input_menu(header, width, prompt, default, numbers_only=True):
    menu_x = int((120 - width) / 2)

    header_height = 2

    menu_h = int(header_height + 1 + 5)
    menu_y = int((50 - menu_h) / 2)

    # create a window

    create_window(menu_x, menu_y, width, menu_h, header)

    blt.puts(menu_x, menu_y, prompt)

    y = menu_y + header_height + 1

    input_str = str(default)

    blt.refresh()
    # present the root console to the player and wait for a key-press
    if numbers_only:
        blt.set('input: filter = [0123456789, enter, backspace]')
    #else:
    #    blt.set('input: filter = [A-z, enter, backspace]')
    while True:
        # take input
        string = blt.read_str(menu_x, y, input_str, 10)
        blt.refresh()

        # after confirming with enter, the function returns the string
        if len(string[1]) > 0:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.clear_area(0, 0, blt.state(blt.TK_WIDTH), blt.state(blt.TK_HEIGHT))
            print("Str" + str(string))
            return string
        else:
            print("Invalid string")
