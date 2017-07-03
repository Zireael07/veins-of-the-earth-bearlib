# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod
from time import time
import json
import bisect

import constants
import renderer
import components


class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False

class obj_Game:
    def __init__(self):
        self.current_map = map_create()
        self.current_entities = []

        self.message_history = []

    def game_message(self, msg, msg_color):
        self.message_history.append((msg, msg_color))

    def add_entity(self, entity):
        if entity is not None:
            self.current_entities.append(entity)


class AI_test:
    def take_turn(self):
        self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1), GAME.current_map)

def death_monster(monster):
    GAME.game_message(monster.creature.name_instance + " is dead!", "gray")
    # clean up components
    monster.creature = None
    monster.ai = None
    # remove from map
    GAME.current_entities.remove(monster)

def map_create():
    new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]

    new_map[10][10].block_path = True
    new_map[12][12].block_path = True

    # walls around the map
    for x in range(constants.MAP_WIDTH):
        new_map[x][0].block_path = True
        new_map[x][constants.MAP_WIDTH-1].block_path = True

    for y in range(constants.MAP_HEIGHT):
        new_map[0][y].block_path = True
        new_map[constants.MAP_HEIGHT-1][y].block_path = True

    map_make_fov(new_map)

    return new_map

def map_make_fov(incoming_map):
    global FOV_MAP

    FOV_MAP = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    for y in range(constants.MAP_HEIGHT):
        for x in range(constants.MAP_WIDTH):
            libtcod.map_set_properties(FOV_MAP, x,y,
                                       not incoming_map[x][y].block_path, not incoming_map[x][y].block_path)

def map_calculate_fov():
    global FOV_CALCULATE

    if FOV_CALCULATE:
        FOV_CALCULATE = False
        libtcod.map_compute_fov(FOV_MAP, PLAYER.x, PLAYER.y, constants.LIGHT_RADIUS, constants.FOV_LIGHT_WALLS,
                                constants.FOV_ALGO)

# def map_check_for_creature(x, y, exclude_entity = None):
#
#     target = None
#
#     # find entity that isn't excluded
#     if exclude_entity:
#         for ent in GAME.current_entities:
#             if (ent is not exclude_entity
#                 and ent.x == x
#                 and ent.y == y
#                 and ent.creature):
#                 target = ent
#
#             if target:
#                 return target
#
#     # find any entity if no exclusions
#     else:
#         for ent in GAME.current_entities:
#             if (ent.x == x
#                 and ent.y == y
#                 and ent.creature):
#                 target = ent


def map_check_for_item(x,y):
    target = None

    for ent in GAME.current_entities:
        if (ent.x == x
            and ent.y == y
            and ent.item):
            target = ent

        if target:
            return target

# the core drawing function
def draw_game(x,y):
    renderer.draw_map(GAME.current_map, FOV_MAP)

    draw_mouseover(x,y)

    blt.color("white")
    for ent in GAME.current_entities:
        ent.draw(fov_map=FOV_MAP)

    renderer.draw_messages(GAME.message_history)


def draw_mouseover(x,y):
    tile_x, tile_y = pix_to_iso(x, y)
    draw_x, draw_y = draw_iso(tile_x, tile_y)

    blt.color("light yellow")
    blt.put(draw_x, draw_y, 0x2317)


# based on STI library for LOVE2D
def draw_iso(x,y):
    # isometric
    offset_x = constants.MAP_WIDTH * 4
    tile_x = (x - y) * constants.TILE_WIDTH / 2 + offset_x
    tile_y = (x + y) * constants.TILE_HEIGHT / 2
    return tile_x, tile_y

def cell_to_iso(x,y):
    offset_x = constants.MAP_WIDTH * 4
    iso_x = y / constants.TILE_HEIGHT + (x - offset_x) / constants.TILE_WIDTH
    iso_y = y / constants.TILE_HEIGHT - (x - offset_x) / constants.TILE_WIDTH
    return iso_x, iso_y


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


def roll(dice, sides):
     result = 0
     for i in range(0, dice, 1):
         roll = libtcod.random_get_int(0, 1, sides)
         result += roll

     print 'Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result)
     return result

def game_main_loop():
    game_quit = False

    fps_update_time = time()
    fps_counter = fps_value = 0

    while not game_quit:

        #clear
        blt.clear()


        blt.puts(2,1, "[color=white]FPS: %d" % (fps_value))

        # mouse test
        blt.puts(
            3, 4,
            "Cursor: [color=orange]%d:%d[/color] [color=dark gray]cells[/color]"
            ", [color=orange]%d:%d[/color] [color=dark gray]pixels[/color]" % (
                blt.state(blt.TK_MOUSE_X),
                blt.state(blt.TK_MOUSE_Y),
                blt.state(blt.TK_MOUSE_PIXEL_X),
                blt.state(blt.TK_MOUSE_PIXEL_Y)))

        # map tile picking test
        # cell_x = blt.state(blt.TK_MOUSE_X)
        # cell_y = blt.state(blt.TK_MOUSE_Y)

        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)

        #blt.puts(2,2, "[color=red] iso coords based on cells: %d %d" % (cell_to_iso(cell_x,cell_y)))
        blt.puts(2,3, "[color=red] iso coords based on pixels: %d %d" % (pix_to_iso(pix_x, pix_y)))

        # mouse picking test
        x = blt.state(blt.TK_MOUSE_X)
        y = blt.state(blt.TK_MOUSE_Y)

        n = 0
        while True:
             code = blt.pick(x, y, n)

             if code == 0: break

             blt.puts(2 + n * 2, 5, u"%c" % (code))
             n += 1
        #
             if n == 0:
                 blt.puts(3, 5, "Empty cell")



        # draw
        draw_game(pix_x, pix_y)

        # debug
        # blt.puts(2,2, "[color=red] player pos in cells: %d %d" % (draw_iso(PLAYER.x, PLAYER.y)))


        # refresh term
        blt.refresh()

        # fps
        fps_counter += 1
        tm = time()
        if tm > fps_update_time + 1:
            fps_value = fps_counter
            fps_counter = 0
            fps_update_time = tm

        # avoid blocking the game with blt.read
        while not game_quit and blt.has_input():


            player_action = game_handle_keys()

            map_calculate_fov()

            if player_action == "QUIT":
                game_quit = True


            if player_action == "mouse_click":
                print "Click"


            if player_action != "no-action" and player_action != "mouse_click":
                for ent in GAME.current_entities:
                    if ent.ai:
                        ent.ai.take_turn()

    # quit the game
    blt.close()

def game_handle_keys():
    global FOV_CALCULATE

    key = blt.read()
    if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
        return "QUIT"

    if key == blt.TK_UP:
        PLAYER.creature.move(0, -1, GAME.current_map)
        FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_DOWN:
        PLAYER.creature.move(0, 1, GAME.current_map)
        FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_LEFT:
        PLAYER.creature.move(-1, 0, GAME.current_map)
        FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_RIGHT:
        PLAYER.creature.move(1, 0, GAME.current_map)
        FOV_CALCULATE = True
        return "player-moved"

    # items
    if key == blt.TK_G:
        object = map_check_for_item(PLAYER.x, PLAYER.y)
        #for obj in objects:
        object.item.pick_up(PLAYER)

    if key == blt.TK_D:
        if len(PLAYER.container.inventory) > 0:
            #drop the last item
            PLAYER.container.inventory[-1].item.drop(PLAYER.x, PLAYER.y)

    if key == blt.TK_I:
        chosen_item = renderer.inventory_menu("Inventory", PLAYER)
        if chosen_item is not None:
            if chosen_item.item:
                chosen_item.item.use(PLAYER)

    if key == blt.TK_C:
        renderer.character_sheet_menu("Character sheet", PLAYER)

    # mouse

    if key == blt.TK_MOUSE_LEFT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)

        click_x, click_y = pix_to_iso(pix_x, pix_y)

        print "Clicked on tile " + str(click_x) + " " + str(click_y)

        if click_x != PLAYER.x or click_y != PLAYER.y:
            PLAYER.creature.move_towards(click_x, click_y, GAME.current_map)
            FOV_CALCULATE = True

        return "player-moved"

    if  key == blt.TK_MOUSE_RIGHT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)
        print "Right clicked on tile " + str(pix_to_iso(pix_x, pix_y))

        return "mouse_click"


    return "no-action"


# def game_message(msg, msg_color):
#     GAME.message_history.append((msg, msg_color))

def game_initialize():
    global GAME, FOV_CALCULATE, PLAYER, ENEMY, ITEM, ITEM2

    blt.open()
    # default terminal size is 80x25
    blt.set("window: size=160x45, cellsize=auto, title='Veins of the Earth'; font: default")

    #vsync
    blt.set("output.vsync=true")

    # mouse
    blt.set("input.filter={keyboard, mouse+}")
    blt.set("input: precise-mouse=true, mouse-cursor=true")

    blt.composition(True)

    # needed to avoid insta-close
    blt.refresh()

    # tiles
    blt.set("0x3002: gfx/floor_sand.png, align=center") # "."
    blt.set("0x23: gfx/wall_stone.png, align=center") # "#"
    blt.set("0x40: gfx/human_m.png, align=center") # "@"
    #NPCs (we use Unicode private area here)
    blt.set("0xE000: gfx/kobold.png,  align=center") # ""
    blt.set("0xE001: gfx/goblin.png, align=center")
    blt.set("0xE002: gfx/drow_fighter.png, align=center")
    blt.set("0xE003: gfx/human.png, align=center")
    #items
    blt.set("0x2215: gfx/longsword.png, align=center") #"∕"
    blt.set("0x1C0: gfx/dagger.png, align=center") # "ǀ"
    blt.set("0xFF3B: gfx/chain_armor.png, align=center") # "［"

    # gfx
    blt.set("0x2317: gfx/mouseover.png, align=center") # "⌗"


    GAME = obj_Game()

    FOV_CALCULATE = True

    # init game for components module
    components.initialize_game(GAME)

    container_com1 = components.com_Container()
    player_array = generate_stats("heroic")
    creature_com1 = components.com_Creature("Player",
                                            base_str=player_array[0], base_dex=player_array[1], base_con=player_array[2],
                                            base_int=player_array[3], base_wis=player_array[4], base_cha=player_array[5])

    PLAYER = components.obj_Actor(1,1, "@", "Player", creature=creature_com1, container=container_com1)

    #test generating items
    GAME.current_entities.append(generate_item(2, 2, "longsword"))
    GAME.current_entities.append(generate_item(3,3, "dagger"))
    GAME.current_entities.append(generate_item(1,1, "chainmail"))

    #test generating monsters
    GAME.add_entity(generate_monster(3, 3, generate_random_mon()))
    GAME.add_entity(generate_monster(5, 5, generate_random_mon()))
    GAME.add_entity(generate_monster(7, 7, generate_random_mon()))
    GAME.add_entity(generate_monster(4, 4, generate_random_mon()))
    GAME.add_entity(generate_monster(8, 8, generate_random_mon()))
    GAME.add_entity(generate_monster(10, 10, generate_random_mon()))
    GAME.add_entity(generate_monster(15, 15, generate_random_mon()))

    # put player last
    GAME.current_entities.append(PLAYER)

    #test
    get_random_item()

# Generating stuff
def generate_item_rarity():
    chances = []
    chances.append(("Mundane", 5))
    chances.append(("Magical", 30))
    chances.append(("Good", 20))
    chances.append(("Rare", 15))
    chances.append(("Excellent", 10))
    chances.append(("Great", 10))
    chances.append(("Unique", 5))

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num + 1
        num += 1 + chance[1]
        # clip top number to 100
        if num > 100:
            num = 100
        chance_roll.append((chance[0], old_num, num))

    #print chance_roll
    return chance_roll

def generate_item_type():
    chances = []
    chances.append(("Item", 15)) # 17 in d20 SRD
    chances.append(("Armor", 35)) # 35 in d20 SRD
    chances.append(("Weapons", 35)) #22 in d20 SRD
    chances.append(("Tools", 15)) #16 in d20 SRD

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num + 1
        num += 1 + chance[1]
        # clip top number to 100
        if num > 100:
            num = 100
        chance_roll.append((chance[0], old_num, num))

    return chance_roll

def get_weapons_bonus_rarity():
    chances = []
    for data_id in weap_bonus_data:
        if 'rarity' in weap_bonus_data[data_id]:
            chances.append((weap_bonus_data[data_id]['name'], weap_bonus_data[data_id]['rarity']))

    print chances

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num+1
        num += 1+chance[1]
        chance_roll.append((chance[0], old_num, num))

    print chance_roll
    return chance_roll

def get_random_weapon_bonus():
    bonus_rarity = get_weapons_bonus_rarity()

    d100 = roll(1, 100)

    breakpoints = [k[2] for k in bonus_rarity]
    breakpoints.sort()

    print breakpoints

    i = bisect.bisect(breakpoints, d100)
    res = bonus_rarity[i][0]
    print "Random weapon bonus is " + res
    return res

def get_armor_material_rarity():
    chances = []
    for data_id in arm_mat_data:
        if 'rarity' in arm_mat_data[data_id]:
            chances.append((arm_mat_data[data_id]['name'], arm_mat_data[data_id]['rarity']))

    print chances

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num+1
        num += 1+chance[1]
        chance_roll.append((chance[0], old_num, num))

    #pad out to 100
    print "Last number is " + str(num)
    chance_roll.append(("None", num, 100))

    print chance_roll

    return chance_roll

def get_random_armor_material():
    material_rarity = get_armor_material_rarity()

    d100 = roll(1, 100)

    breakpoints = [k[2] for k in material_rarity]
    breakpoints.sort()

    print breakpoints

    i = bisect.bisect(breakpoints, d100)
    res = material_rarity[i][0]
    print "Random material is " + res
    return res


def get_random_item():
    item_rarity = generate_item_rarity()

    d100 = roll(1, 100)

    breakpoints = [k[2] for k in item_rarity]
    breakpoints.sort()

    print breakpoints

    i = bisect.bisect(breakpoints, d100)
    res = item_rarity[i][0]
    print "Random item rarity is " + res

    # generate item type
    item_types = generate_item_type()
    d100 = roll(1, 100)

    breakpoints = [k[2] for k in item_types]
    breakpoints.sort()

    print breakpoints

    i = bisect.bisect(breakpoints, d100)
    it_type = item_types[i][0]
    print "Random item type is " + it_type

    # if armor, random material
    if it_type == "Armor":
        get_random_armor_material()

    if it_type == "Weapons" and res is not "Mundane":
        get_random_weapon_bonus()


    # return res

def get_monster_chances():
    chances = []
    for data_id in monster_data:
        if monster_data[data_id]['rarity']:
            chances.append((monster_data[data_id]['name'], monster_data[data_id]['rarity']))

    print chances

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num+1
        num += 1+chance[1]
        chance_roll.append((chance[0], old_num, num))

    #pad out to 100
    print "Last number is " + str(num)
    chance_roll.append(("None", num, 100))

    print chance_roll

    return chance_roll


def generate_random_mon():
    mon_chances = get_monster_chances()

    d100 = roll(1, 100)

    #print "Rolled " + str(d100) + " on random monster gen table"

    breakpoints = [k[2] for k in mon_chances]
    breakpoints.sort()

    print breakpoints


    i = bisect.bisect(breakpoints, d100)
    res = mon_chances[i][0]
    print "Random monster is " + res
    return res


def generate_stats(array="standard", kind="melee"):
    if array == "heroic":
        array = [ 15, 14, 13, 12, 10, 8]
    else:
        array = [ 13, 12, 11, 10, 9, 8]

    if kind == "ranged":
        # STR DEX CON INT WIS CHA
        temp = []
        temp.insert(0, array[2])
        temp.insert(1, array[0])
        temp.insert(2, array[1])
        temp.insert(3, array[3])
        temp.insert(4, array[4])
        temp.insert(5, array[5])
    else:
        print "Using default array"
        # STR DEX CON INT WIS CHA
        temp = []
        temp.insert(0, array[0])
        temp.insert(1, array[2])
        temp.insert(2, array[1])
        temp.insert(3, array[4])
        temp.insert(4, array[3])
        temp.insert(5, array[5])


    return temp

def generate_monster(x,y, id):
    if id == 'None' or id == None:
        print "Wanted id of None, aborting"
        return

    print "Generating monster with id " + id + " at " + str(x) + " " + str(y)

    # Set values
    mon_name = monster_data[id]['name']
    mon_hp = monster_data[id]['hit_points']
    mon_dam_num = monster_data[id]['damage_number']
    mon_dam_dice = monster_data[id]['damage_dice']
    # make it a hex value
    char = int(monster_data[id]['char'], 16)

    # Defaults
    death = death_monster

    #Create the monster
    mon_array = generate_stats()
    creature_comp = components.com_Creature(mon_name,
                                            base_str=mon_array[0], base_dex=mon_array[1], base_con=mon_array[2],
                                            base_int=mon_array[3], base_wis=mon_array[4], base_cha=mon_array[5],
                                            death_function=death)
    ai_comp = AI_test()

    monster = components.obj_Actor(x,y, char, mon_name, creature=creature_comp, ai=ai_comp)

    return monster

def generate_item(x, y, id):
    print "Generating item with id " + id + " at " + str(x) + " " + str(y)

    # set values
    item_name = items_data[id]['name']
    item_slot = items_data[id]['slot']
    # make it a hex value
    item_char = int(items_data[id]['char'], 16)
    item_type = items_data[id]['type']

    # optional parameters depending on type
    if item_type == "weapon":
        item_dice = items_data[id]['damage_number']
        item_sides = items_data[id]['damage_dice']

    if item_type == "armor":
        item_armor = items_data[id]['combat_armor']


    # Create the item
    eq_com = components.com_Equipment(item_slot)
    item_com = components.com_Item()
    item = components.obj_Actor(x,y, item_char, item_name, item=item_com, equipment=eq_com)

    return item

if __name__ == '__main__':

    # Load JSON
    with open(constants.NPC_JSON_PATH) as json_data:
        monster_data = json.load(json_data)
        #print monster_data

    with open(constants.ITEMS_JSON_PATH) as json_data:
        items_data = json.load(json_data)
        #print items_data

    with open("data/armor_materials.json") as json_data:
        arm_mat_data = json.load(json_data)
        print arm_mat_data

    with open("data/armor_bonuses.json") as json_data:
        arm_bonus_data = json.load(json_data)
        print arm_bonus_data

    with open("data/armor_properties.json") as json_data:
        arm_prop_data = json.load(json_data)
        print arm_prop_data

    with open("data/weapons_bonuses.json") as json_data:
        weap_bonus_data = json.load(json_data)
        print weap_bonus_data

    with open("data/weapons_properties.json") as json_data:
        weap_prop_data = json.load(json_data)
        print weap_prop_data

    game_initialize()
    game_main_loop()


