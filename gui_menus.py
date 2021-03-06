# coding: utf8

import sys
from bearlibterminal import terminal as blt

import constants
from map_common import get_map_string
from generators import roll
import gui_renderer

import game_vars


def main_menu():

    key = gui_renderer.menu_colored("MAIN MENU", [("(S)tart new game", "white"), ("(L)oad game", "white"),
                                              ("(O)ptions", "white"),
                                              ("(E)xit game", "white")],
                       50, menu_x = int((180 - 50) / 2), border=False)

    if key == blt.TK_S or key == 0:
        return 1
    if key == blt.TK_L or key == 1:
        return 2
    if key == blt.TK_O or key == 2:
        return 3

def options_menu_outer():
    ret = options_menu()
    if ret is not None:
        # if we are getting input, keep showing the log
        while ret is not None:
            print("Option is: " + str(ret))
            if ret == 1:
                print("Option 1 toggled")
                # toggle
                constants.VI_KEYS = not constants.VI_KEYS

            ret = options_menu()

        print("Ret:" + str(ret))
        return ret

def options_menu():
    opts = [("(V)i keys: %s " % (str(constants.VI_KEYS)), "white")]

    key = gui_renderer.menu_colored("OPTIONS", opts, 50, menu_x = int((180 - 50)/2), border=False)

    if key == blt.TK_V or key == 0:
        return 1
    else:
        return None # exit

# individual menus
def character_sheet_menu(header, player):
    options = [("Race:" + str(player.name), "white"), ("Gender: " + str(player.creature.gender), "white"),
                ("STR: " + str(player.creature.strength), "white"), ("DEX: " + str(player.creature.dexterity), "white"),
               ("CON: " + str(player.creature.constitution), "white"), ("INT: " + str(player.creature.intelligence), "white"),
                ("WIS: " + str(player.creature.wisdom), "white"), ("CHA: " + str(player.creature.charisma), "white"),
               ("Attack: " + str(player.creature.melee), "white"), ("Dodge: " + str(player.creature.dodge), "white"),
               #("Armor defense: " + str(player.creature.defense) + str(player.creature.defense_str), "white"),
               ("Light: " + str(player.creature.get_light_radius()), "yellow"),
               ("", "white"),
               (str(game_vars.calendar_game.get_time_date(game_vars.calendar_game.turn)), "yellow"),
               ("Armor defense:", "white")
               ]

    for p in player.creature.body_parts:
        options.append((str(p.name) + ": " + str(p.defense), "white"))

    for m in player.creature.player.money:
        options.append((str(m[0]) + ": " + str(m[1]), "amber"))


    for ef in player.creature.effects:
        options.append(("", "white"))
        options.append((ef.name, "green"))

    index = gui_renderer.menu_colored(header + ": " + player.creature.name_instance, options, 50, 'CHARACTER SHEET')

    if index is None:
        return None


def log_menu_inner(header, begin, end):
    options = game_vars.message_history

    scroll = gui_renderer.menu_colored_scrolled(header, options, 50, begin, end, 'LOG HISTORY')

    return scroll

# TODO: kills performance on the dumpster, investigate
def log_menu(header, begin, end):
    ret, begin, end = log_menu_inner(header, begin, end)
    while ret is not None:
         print(ret)
        # if we are getting input, keep showing the log
#        while ret is not None:
         if end + ret > len(game_vars.message_history)-1:
            # do nothing if we'd scroll past the end
            end = end
            begin = begin
         if begin + ret < 0:
                # if we would scroll past 0, do nothing
            begin = 0
            end = end
         if begin + ret >= 0 and end + ret <= len(game_vars.message_history)-1:
                # print("Proceed normally")
            begin = begin + ret
            end = end + ret

         # print("ret " + str(ret) + "Begin " + str(begin) + " end" + str(end))
         ret, begin, end = log_menu_inner("Log history", begin, end)


def dmg_menu(header, opt):
    # flatten
    flat_list = [item for sublist in opt for item in sublist]

    options = []

    #for o in opt:
    for o in flat_list:
        options.append(str(o))

    index = gui_renderer.options_menu(header, options, 30)

    if index is None:
        return None


def display_dmg_window(index):
    #if "damage" in game.message_history[index][0]:
        #print("The line says damage!")

        # extract the dmg number
        #dmg = filter(str.isdigit, str(game.message_history[index][0]))
        #dmg_menu(dmg)

    if game_vars.message_history[index][2] is not None:
        if "damage" in game_vars.message_history[index][0]:
            dmg_menu("damage", game_vars.message_history[index][2])

def dialogue_window(creature, player, items):
    blt.layer(1)

    if not player.speak_same_language(creature):
        # debug
        print(player.name_instance + " and " + creature.name_instance + " don't know same language")
        # this reportedly doesn't work for Unicode - luckily, no Unicode in our prewritten dialogues!
        #import codecs
        #chat = codecs.encode(creature.chat['chat'], 'rot_13')

        # test
        print(creature.chat['chat'])

        import languages
        lang = languages.Language(20)

        import re
        re_word = re.compile(r'\w+')

        # this preserves punctuation since we just do replacement word-by-word
        chat = re_word.sub(lang.language_replace, creature.chat['chat'])

        chat = str(chat)

        # don't show any answers
        answers = []
    else:
        chat = creature.chat['chat']
        answers = creature.chat['answer']

    index = gui_renderer.dialogue_menu(creature.name_instance, 50, "DIALOGUE", chat, answers)

    if index is not None and creature.chat['answer'][index]:
        #print("Index " + str(index) + " " + str(creature.chat['answer'][index]['reply']))
        reply = creature.chat['answer'][index]['reply']
        action = creature.chat['answer'][index]['action'] if 'action' in creature.chat['answer'][index] else None
        print("Action is: " + str(action))

        # repeated bit
        if not player.speak_same_language(creature):
            import codecs
            chat = codecs.encode(creature.chat[reply], 'rot_13')
        else:
            chat = creature.chat[reply]

        # this resets the index!
        index = gui_renderer.dialogue_menu(creature.name_instance, 50, "DIALOGUE", chat, [])

        # TODO: move individual action code out of here
        if action == "shop":
            # test shop
            item, buy = shop_window(player, creature, items)

            # transfer item to player
            if item is not None:
                if buy:
                    if player.player.check_money("silver", item.item.price/10):
                        # test
                        player.player.remove_money([("silver", item.item.price/10)])
                        item.item.pick_up(player.owner)
                else:
                    player.player.add_money([("silver", item.item.price/10)])
                    item.item.current_container.inventory.remove(item)
                    creature.shop = []
                    creature.shop.append(item)

        if action == "hooker":
            if player.player.check_money("silver", 10):
                player.player.remove_money([("silver", 10)])
                player.player.city_rest()

                # spawn kid
                player.player.generate_kid()


def shop_window(player, creature, items):
    player_inv = [item.display_name() + " (" + str(item.item.price) + ")" for item in player.owner.container.inventory]

    if not hasattr(creature, 'shop'):
        creature.shop = []

    for item in items:
        creature.shop.append(item)
    shop_inv = [item.display_name() + " (" + str(item.item.price) + ")" for item in creature.shop]
    columns = [player_inv, shop_inv]

    # we want one item selected (for now)
    index = gui_renderer.multicolumn_menu("SHOP", columns, 80, 50)
    print("Ind: " + str(index))



    if index is None:
        return None, False
    else:
        if index[0] > len(player_inv)-1:
            num = index[0]-len(player_inv)
            print("NPC item" + str(num))

            # return item
            return creature.shop[num], True
        else:
            num = index[0]
            print("Own item num " + str(num))
            # return item
            return player.owner.container.inventory[num], False


def help_menu():
    with open("data/help.txt") as help_f:
        help_t = help_f.read()
    # make possible drawing the >
    blt.set("0x003E: none")
    gui_renderer.text_menu("Keybindings", 70, "HELP",
                help_t)
    # restore drawing
    blt.set("0x003E: gfx/stairs_down.png, align=center")


def debug_menu(player):

    options = ["Reveal map", "Map overview", "Creatures list", "Spawn creature", "Spawn item", "Items list", "Change level"]

    key = gui_renderer.options_menu("DEBUG", options, 50, "Debug menu")

    print("key: " + str(key))

    if key == 0:
        print("Debug mode on")
        constants.DEBUG = True

        # force redraw
        return "redraw"
    if key == 1:

        # make possible drawing the characters
        blt.set("0x003E: none")
        blt.set("0x3002: none")
        blt.set("0x23: none")

        gui_renderer.text_menu("Map", 50, "MAP OVERVIEW", get_map_string(game_vars.level.current_map))

        # restore drawing
        blt.set("0x003E: gfx/stairs_down.png, align=center")
        blt.set("0x3002: gfx/floor_cave.png, align=center")
        blt.set("0x23: gfx/wall_stone.png, align=center")

        # force redraw
        return "redraw"

    if key == 2:

        opt = []
        for ent in game_vars.level.current_entities:
            if ent.creature:
                opt.append(ent.creature.name_instance + " X: " + str(ent.x) + " Y: " + str(ent.y))

        gui_renderer.options_menu("Creature list", opt, 50, "List")

    if key == 3:
        import generators
        # load
        #with open(constants.NPC_JSON_PATH) as json_data:
        #    monster_data = json.load(json_data)


        opt = []
        for m_id in generators.monster_data:
            opt.append(m_id)

        sel = gui_renderer.options_menu("Spawn creature:", opt, 50, "List")

        if sel is not None:
            game_vars.level.add_entity(generators.generate_monster(opt[sel], player.x, player.y))
            # force redraw
            return "redraw"

    if key == 4:
        import generators

        opt = []
        for i_id in generators.items_data:
            opt.append(i_id)

        sel = gui_renderer.options_menu("Spawn item:", opt, 50, "List")

        if sel is not None:
            item = generators.generate_item(opt[sel], player.x, player.y)
            game_vars.level.add_entity(item)
            if item:
                item.send_to_back()
            # force redraw
            return "redraw"
    if key == 5:

        opt = []
        for ent in game_vars.level.current_entities:
            if not ent.creature:
                opt.append(ent.name + " X: " + str(ent.x) + " Y: " + str(ent.y))

        gui_renderer.options_menu("Item list", opt, 50, "List")

    if key == 6:
        import level
        opt = []

        for l in level.levels_data:
            opt.append(l)

        sel = gui_renderer.options_menu("Go to level:", opt, 50, "List")

        if sel is not None:
            print("Selected: " + str(opt[sel]))
            game_vars.game_obj.next_level(opt[sel])
            # force redraw
            return "redraw"

def character_stats_menu_outer(player):
    ret = character_stats_menu(player)
    if ret is not None:
        # if we are getting input, keep showing the log
        while ret is not None:
            ret = character_stats_menu(player)

        return ret

def character_stats_menu(player):
    options = [("STR: " + str(player.creature.strength), "white"),
               ("DEX: " + str(player.creature.dexterity) + str(player.creature.display_stat_bonus('dexterity')), "white"),
               ("CON: " + str(player.creature.constitution) + str(player.creature.display_stat_bonus('constitution')), "white"),
               ("INT: " + str(player.creature.intelligence) + str(player.creature.display_stat_bonus('dexterity')), "white"),
               ("WIS: " + str(player.creature.wisdom), "white"),
               ("CHA: " + str(player.creature.charisma), "white"),
               ("(R)eroll!", "yellow"), ("(P)roceed", "white")]

    key = gui_renderer.menu_colored("STATS", options, 50, 'CHARACTER CREATION II')

    if key == blt.TK_R:
        # reroll
        player.creature.strength = roll(3,6)
        player.creature.dexterity = roll(3,6)
        player.creature.constitution = roll(3,6)
        player.creature.intelligence = roll(3,6)
        player.creature.wisdom = roll(3,6)
        player.creature.charisma = roll(3,6)
        return True
    elif key == blt.TK_P or key == blt.TK_ESCAPE:
        # exit the window
        return None
    else:
        # redraw
        return True

def character_creation_menu(player):
    races = ["human", "drow"]
    genders = ["male", "female"]

    columns = [races, genders]

    tiles = ["gfx/human_m.png", "gfx/drow_m.png", "gfx/human_f.png", "gfx/drow_f.png"]

    key = gui_renderer.multicolumn_menu("CHARACTER CREATION", columns, 80, 10, 2)

    if key is not None:
        if 0 in key and 2 in key:
            select = tiles[0]
            player.creature.gender = "male"
            player.name = "human"
        if 0 in key and 3 in key:
            select = tiles[2]
            player.creature.gender = "female"
            player.name = "human"
        if 1 in key and 2 in key:
            select = tiles[1]
            player.creature.gender = "male"
            player.name = "drow"
        if 1 in key and 3 in key:
            select = tiles[3]
            player.creature.gender = "female"
            player.name = "drow"

        blt.set("0x40: " + select + ", align=center")  # "@"

        #print("Selected: " + str(select))

        # step II - character stats
        blt.clear()
        character_stats_menu_outer(player)

        # welcome!
        blt.clear()

        player.creature.name_instance = character_name_input()
        player.creature.apply_stat_bonuses()

        blt.clear()
        # TODO: text wrap
        with open("data/welcome.txt") as welcome_f:
            welcome = welcome_f.read()

        gui_renderer.text_menu("", 70, "Welcome to Veins of the Earth",
                  welcome)

    # pressed ESC while in character creation I
    else:
        print("Pressed ESC")
        # quit cleanly
        sys.exit()

def character_name_input():
    name = gui_renderer.input_menu("Character name: ", 50, "Name", "Zir", False)
    print("Inputed name: " + str(name))
    return str(name[1])

def inventory_menu(header, player):
    index = gui_renderer.inventory_menu_test(header, 50, 'INVENTORY', player.container.equipped_items, player.container.inventory)

    #if an item was chosen, return it
    if index is None or len(player.container.inventory) == 0:
         return None
    return player.container.inventory[index]


def item_actions_menu(item):
    options = ["Use/wear", "Drop"]

    index = gui_renderer.options_menu(item.display_name(), options, 20, "Item actions", 5)

    if index is None:
        return None

    return index

def drop_menu(player):
    if len(player.container.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.display_name() for item in player.container.inventory]

    index = gui_renderer.options_menu("Drop item", options, 50, "DROP")

    return index

def pickup_menu(entities):
    options = [ent.name for ent in entities]

    index = gui_renderer.options_menu("Pick item", options, 50, "Pick up")

    if index is None:
        return None
    else:
        return entities[index]

def seed_input_menu():
    seed = gui_renderer.input_menu("Seed", 50, "Seed (numbers only):", 2)
    print("Inputed seed: " + str(seed))
    return int(seed[1])

def death_menu(player):
    if len(player.creature.player.kids) == 0:
        options = ['No children']
    else:
        options = [ent.name for ent in player.creature.player.kids]

    index = gui_renderer.options_menu("Choose child", options, 50, "You are DEAD!")

    if len(player.creature.player.kids) == 0:
        return None
    else:
        return player.creature.player.kids[index]
