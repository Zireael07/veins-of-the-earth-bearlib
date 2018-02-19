# coding: utf8

from bearlibterminal import terminal as blt

import constants
from map_common import get_map_string
from generators import roll
import renderer

def initialize_game(game):
    global GAME
    GAME = game


def main_menu():

    key = renderer.menu_colored("MAIN MENU", [("(S)tart new game", "white"), ("(L)oad game", "white"), ("(E)xit game", "white")],
                       50, menu_x = int((180 - 50) / 2), border=False)

    if key == blt.TK_S:
        return 1
    if key == blt.TK_L:
        return 2

# individual menus
def character_sheet_menu(header, player):
    options = [("STR: " + str(player.creature.strength), "white"), ("DEX: " + str(player.creature.dexterity), "white"),
               ("CON: " + str(player.creature.constitution), "white"), ("INT: " + str(player.creature.intelligence), "white"),
                ("WIS: " + str(player.creature.wisdom), "white"), ("CHA: " + str(player.creature.charisma), "white"),
               ("Attack: " + str(player.creature.melee), "white"), ("Dodge: " + str(player.creature.dodge), "white"),
               ("Armor defense: " + str(player.creature.defense) + str(player.creature.defense_str), "white"),
               ("", "white"),
               (str(GAME.calendar.get_time_date(GAME.calendar.turn)), "yellow")
               ]

    for m in player.creature.player.money:
        options.append((str(m[0]) + ": " + str(m[1]), "amber"))


    for ef in player.creature.effects:
        options.append(("", "white"))
        options.append((ef.name, "green"))

    index = renderer.menu_colored(header, options, 50, 'CHARACTER SHEET')

    if index is None:
        return None


def log_menu_inner(header, begin, end):
    options = GAME.message_history

    scroll = renderer.menu_colored_scrolled(header, options, 50, begin, end, 'LOG HISTORY')

    return scroll

def log_menu(header, begin, end):
    ret, begin, end = log_menu_inner(header, begin, end)
    if ret is not None:
        # if we are getting input, keep showing the log
        while ret is not None:
            if end + ret > len(GAME.message_history) - 1:
                # do nothing if we'd scroll past the end
                end = end
                begin = begin
            if begin + ret < 0:
                # if we would scroll past 0, do nothing
                begin = 0
                end = end
            if begin + ret > 0 and end + ret <= len(GAME.message_history) - 1:
                # print("Proceed normally")
                begin = begin + ret
                end = end + ret

            # print("ret " + str(ret) + "Begin " + str(begin) + " end" + str(end))
            ret, begin, end = log_menu_inner("Log history", begin, end)


def dmg_menu(header):
    options = ["Damage display"]
    index = renderer.options_menu(header, options, 30)

    if index is None:
        return None


def display_dmg_window(index):
    if "damage" in GAME.message_history[index][0]:
        #print("The line says damage!")

        # extract the dmg number
        dmg = filter(str.isdigit, str(GAME.message_history[index][0]))
        dmg_menu(dmg)

def dialogue_window(creature):
    blt.layer(1)
    index = renderer.dialogue_menu(creature.name_instance, 50, "DIALOGUE", creature.chat['chat'], creature.chat['answer'])

    if index is not None and creature.chat['answer'][index]:
        print("Index " + str(index) + " " + str(creature.chat['answer'][index]['reply']))
        reply = creature.chat['answer'][index]['reply']
        index = renderer.dialogue_menu(creature.name_instance, 50, "DIALOGUE", creature.chat[reply], [])


def help_menu():
    # make possible drawing the >
    blt.set("0x003E: none")
    renderer.text_menu("Keybindings", 70, "HELP", "Arrows to move" + "\n" + " > to ascend/descend stairs" + \
                "\n" + "G to pick up items, D to drop items, I to open inventory" + \
                "\n" + "C to open character sheet, L to open log" + \
                "\n" + "? to bring up this menu again")
    # restore drawing
    blt.set("0x003E: gfx/stairs_down.png, align=center")


def debug_menu(player):

    options = ["Reveal map", "Map overview", "Creatures list", "Spawn creature"]

    key = renderer.options_menu("DEBUG", options, 50, "Debug menu")

    print("key: " + str(key))

    if key == 0:
        print("Debug mode on")
        constants.DEBUG = True
    if key == 1:

        # make possible drawing the characters
        blt.set("0x003E: none")
        blt.set("0x3002: none")
        blt.set("0x23: none")

        renderer.text_menu("Map", 50, "MAP OVERVIEW", get_map_string(GAME.level.current_map))

        # restore drawing
        blt.set("0x003E: gfx/stairs_down.png, align=center")
        blt.set("0x3002: gfx/floor_cave.png, align=center")
        blt.set("0x23: gfx/wall_stone.png, align=center")

    if key == 2:

        opt = []
        for ent in GAME.level.current_entities:
            if ent.creature:
                opt.append(ent.creature.name_instance + " X: " + str(ent.x) + " Y: " + str(ent.y))

        renderer.options_menu("Creature list", opt, 50, "List")

    if key == 3:
        import generators
        # load
        #with open(constants.NPC_JSON_PATH) as json_data:
        #    monster_data = json.load(json_data)


        opt = []
        for m_id in generators.monster_data:
            opt.append(m_id)

        sel = renderer.options_menu("Spawn creature:", opt, 50, "List")

        if sel is not None:
            GAME.level.add_entity(generators.generate_monster(opt[sel], player.x, player.y))

def character_stats_menu_outer(player):
    ret = character_stats_menu(player)
    if ret is not None:
        # if we are getting input, keep showing the log
        while ret is not None:
            ret = character_stats_menu(player)

        return ret

def character_stats_menu(player):
    options = [("STR: " + str(player.creature.strength), "white"), ("DEX: " + str(player.creature.dexterity), "white"),
               ("CON: " + str(player.creature.constitution), "white"),
               ("INT: " + str(player.creature.intelligence), "white"),
               ("WIS: " + str(player.creature.wisdom), "white"), ("CHA: " + str(player.creature.charisma), "white"),
               ("(R)eroll!", "yellow"), ("(E)xit", "white")]

    key = renderer.menu_colored("STATS", options, 50, 'CHARACTER CREATION II')

    if key == blt.TK_R:
        # reroll
        player.creature.strength = roll(3,6)
        player.creature.dexterity = roll(3,6)
        player.creature.constitution = roll(3,6)
        player.creature.intelligence = roll(3,6)
        player.creature.wisdom = roll(3,6)
        player.creature.charisma = roll(3,6)
        return True
    elif key == blt.TK_E or key == blt.TK_ESCAPE:
        # exit
        return None
    else:
        # redraw
        return True

def character_creation_menu(player):
    races = ["human", "drow"]
    genders = ["male", "female"]

    columns = [races, genders]

    tiles = ["gfx/human_m.png", "gfx/drow_m.png", "gfx/human_f.png", "gfx/drow_f.png"]

    key = renderer.multicolumn_menu("CHARACTER CREATION", columns, 80)

    if 0 in key and 2 in key:
        select = tiles[0]
    if 0 in key and 3 in key:
        select = tiles[2]
    if 1 in key and 2 in key:
        select = tiles[1]
    if 1 in key and 3 in key:
        select = tiles[3]

    blt.set("0x40: " + select + ", align=center")  # "@"

    #print("Selected: " + str(select))

    # step II - character stats
    blt.clear()
    opt = character_stats_menu_outer(player)

    # welcome!
    blt.clear()
    # TODO: text wrap
    renderer.text_menu("", 70, "Welcome to Veins of the Earth",
              """Brave adventurer, you are now lost in the underground corridors 
of the Veins of the Earth. 
There is no way to return to your homeland.
How long can you survive...?
Press ESC or click to close.""")

def inventory_menu(header, player):
    index = renderer.inventory_menu_test(header, 50, 'INVENTORY', player.container.equipped_items, player.container.inventory)

    #if an item was chosen, return it
    if index is None or len(player.container.inventory) == 0:
         return None
    return player.container.inventory[index]

def drop_menu(player):
    if len(player.container.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.display_name() for item in player.container.inventory]

    index = renderer.options_menu("Drop item", options, 50, "DROP")

    return index

def pickup_menu(entities):
    options = [ent.name for ent in entities]

    index = renderer.options_menu("Pick item", options, 50, "Pick up")

    if index is None:
        return None
    else:
        return entities[index]
