# coding: utf8
import libtcodpy as libtcod
import bisect
import json
import math

import components
import constants

import logging
from logging.config import dictConfig

# need a reference to global GAME %^$@
def initialize_game(game):
    global GAME

    GAME = game


def roll(dice, sides):
    result = 0
    for i in range(0, dice, 1):
        roll = libtcod.random_get_int(0, 1, sides)
        result += roll

    logger.info('Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result))
    #print 'Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result)
    return result



# AI
class AI_test(object):
    def take_turn(self, player):
        print("AI taking turn")
        # check distance to player
        dx = player.x - self.owner.x
        dy = player.y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        print("Distance to player is " + str(distance))

        if distance > 5:
            print("AI distance > 5, random move")
            self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1), GAME.current_map)
        else:
            print("AI distance less than 5, moving towards player")
            self.owner.creature.move_towards(player.x, player.y, GAME.current_map)

def death_monster(monster):
    GAME.game_message(monster.creature.name_instance + " is dead!", "gray")
    # clean up components
    monster.creature = None
    monster.ai = None
    # remove from map
    GAME.current_entities.remove(monster)


# Generating stuff
# Item generation
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

    #print chances
    logger.debug(chances)

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num+1
        num += 1+chance[1]
        chance_roll.append((chance[0], old_num, num))

    #print chance_roll
    logger.debug(chance_roll)
    return chance_roll

def get_random_weapon_bonus():
    bonus_rarity = get_weapons_bonus_rarity()

    d100 = roll(1, 100)

    breakpoints = [k[2] for k in bonus_rarity]
    breakpoints.sort()

    #print breakpoints
    logger.debug(breakpoints)

    i = bisect.bisect(breakpoints, d100)
    res = bonus_rarity[i][0]
    print "Random weapon bonus is " + res
    return res

def get_armor_material_rarity():
    chances = []
    for data_id in arm_mat_data:
        if 'rarity' in arm_mat_data[data_id]:
            chances.append((arm_mat_data[data_id]['name'], arm_mat_data[data_id]['rarity']))

    #print chances
    logger.debug(chances)

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num+1
        num += 1+chance[1]
        chance_roll.append((chance[0], old_num, num))

    #pad out to 100
    logger.debug("Last number is " + str(num))
    #print "Last number is " + str(num)
    chance_roll.append(("None", num, 100))

    #print chance_roll
    logger.debug(chance_roll)

    return chance_roll

def get_random_armor_material():
    material_rarity = get_armor_material_rarity()

    d100 = roll(1, 100)

    breakpoints = [k[2] for k in material_rarity if k[2] < 100]
    breakpoints.sort()

    #print breakpoints
    logger.debug(breakpoints)

    i = bisect.bisect(breakpoints, d100)
    res = material_rarity[i][0]
    logger.info("Random material is " + res)
    #print "Random material is " + res
    return res


def get_random_item():
    item_rarity = generate_item_rarity()

    d100 = roll(1, 100)

    breakpoints = [k[2] for k in item_rarity if k[2] < 100]
    breakpoints.sort()

    #print breakpoints
    logger.debug(breakpoints)

    i = bisect.bisect(breakpoints, d100)
    res = item_rarity[i][0]
    logger.info("Random item rarity is " + res)
    #print "Random item rarity is " + res

    # generate item type
    item_types = generate_item_type()
    d100 = roll(1, 100)

    breakpoints = [k[2] for k in item_types if k[2] < 100]
    breakpoints.sort()

    logger.debug(breakpoints)
    #print breakpoints

    i = bisect.bisect(breakpoints, d100)
    it_type = item_types[i][0]
    logger.info("Random item type is " + it_type)
    #print "Random item type is " + it_type

    # if armor, random material
    if it_type == "Armor":
        get_random_armor_material()

    if it_type == "Weapons" and res is not "Mundane":
        get_random_weapon_bonus()


    # return res

# X,Y need to come after id so that we can use tuple unpacking here (Python 2.7.x)
def generate_item(i_id, x,y):
    logger.info("Generating item with id " + i_id + " at " + str(x) + " " + str(y))
    #print "Generating item with id " + i_id + " at " + str(x) + " " + str(y)

    # set values
    item_name = items_data[i_id]['name']
    item_slot = items_data[i_id]['slot']
    # make it a hex value
    item_char = int(items_data[i_id]['char'], 16)
    item_type = items_data[i_id]['type']

    # optional parameters depending on type
    if item_type == "weapon":
        item_dice = items_data[i_id]['damage_number']
        item_sides = items_data[i_id]['damage_dice']

    if item_type == "armor":
        item_armor = items_data[i_id]['combat_armor']


    # Create the item
    eq_com = components.com_Equipment(item_slot)
    item_com = components.com_Item()
    item = components.obj_Actor(x,y, item_char, item_name, item=item_com, equipment=eq_com)

    return item

# Monster generation
def get_monster_chances():
    chances = []
    for data_id in monster_data:
        if monster_data[data_id]['rarity']:
            chances.append((monster_data[data_id]['name'], monster_data[data_id]['rarity']))

    #print chances
    logger.debug(chances)

    num = 0
    chance_roll = []
    for chance in chances:
        old_num = num+1
        num += 1+chance[1]
        chance_roll.append((chance[0], old_num, num))

    #pad out to 100
    #print "Last number is " + str(num)
    logger.debug("Last number is " + str(num))
    chance_roll.append(("None", num, 100))

    #print chance_roll

    return chance_roll


def generate_random_mon():
    mon_chances = get_monster_chances()

    d100 = roll(1, 100)

    #print "Rolled " + str(d100) + " on random monster gen table"

    breakpoints = [k[2] for k in mon_chances if k[2] != 100]
    breakpoints.sort()

    #print breakpoints
    logger.debug(breakpoints)

    i = bisect.bisect(breakpoints, d100)
    res = mon_chances[i][0]
    logger.info("Random monster is " + res)
    #print "Random monster is " + res
    return res

def test_force_roll(force):
    print("Test forcing a roll of " + str(force))
    mon_chances = get_monster_chances()

    d100 = force

    breakpoints = [k[2] for k in mon_chances if k[2] != 100]
    breakpoints.sort()

    #print breakpoints
    logger.debug(breakpoints)

    i = bisect.bisect(breakpoints, d100)
    res = mon_chances[i][0]
    logger.info("Random monster is " + res)
    #print "Random monster is " + res
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
        #print "Using default array"
        # STR DEX CON INT WIS CHA
        temp = []
        temp.insert(0, array[0])
        temp.insert(1, array[2])
        temp.insert(2, array[1])
        temp.insert(3, array[4])
        temp.insert(4, array[3])
        temp.insert(5, array[5])


    return temp

# X,Y need to come after ID because we want to use tuple unpacking
def generate_monster(m_id, x,y):
    if m_id == 'None' or m_id == None:
        logger.info("Wanted id of None, aborting")
        #print "Wanted id of None, aborting"
        return

    logger.info("Generating monster with id " + m_id + " at " + str(x) + " " + str(y))
    #print "Generating monster with id " + m_id + " at " + str(x) + " " + str(y)

    # Set values
    mon_name = monster_data[m_id]['name']
    mon_hp = monster_data[m_id]['hit_points']
    mon_dam_num = monster_data[m_id]['damage_number']
    mon_dam_dice = monster_data[m_id]['damage_dice']
    mon_faction = monster_data[m_id]['faction']
    # make it a hex value
    char = int(monster_data[m_id]['char'], 16)

    if 'text' in monster_data[m_id]:
        mon_text = monster_data[m_id]['text']
    else:
        mon_text = None

    # Defaults
    death = death_monster

    #Create the monster
    mon_array = generate_stats()
    creature_comp = components.com_Creature(mon_name,
                                            base_str=mon_array[0], base_dex=mon_array[1], base_con=mon_array[2],
                                            base_int=mon_array[3], base_wis=mon_array[4], base_cha=mon_array[5],
                                            faction=mon_faction,
                                            text = mon_text,
                                            death_function=death)
    ai_comp = AI_test()

    monster = components.obj_Actor(x,y, char, mon_name, creature=creature_comp, ai=ai_comp)

    return monster


# Execute
# Load logger settings
with open("logging.json") as js_config_data:
    config_data = json.load(js_config_data)
    dictConfig(config_data)

    logger = logging.getLogger()


# Load JSON
with open(constants.NPC_JSON_PATH) as json_data:
    monster_data = json.load(json_data)
    logger.debug(monster_data)

    #print monster_data

with open(constants.ITEMS_JSON_PATH) as json_data:
    items_data = json.load(json_data)
    logger.debug(items_data)
    #print items_data

with open("data/armor_materials.json") as json_data:
    arm_mat_data = json.load(json_data)
    logger.debug(arm_mat_data)
    #print arm_mat_data

with open("data/armor_bonuses.json") as json_data:
    arm_bonus_data = json.load(json_data)
    logger.debug(arm_bonus_data)
    #print arm_bonus_data

with open("data/armor_properties.json") as json_data:
    arm_prop_data = json.load(json_data)
    logger.debug(arm_prop_data)
    #print arm_prop_data

with open("data/weapons_bonuses.json") as json_data:
    weap_bonus_data = json.load(json_data)
    logger.debug(weap_bonus_data)
    #print weap_bonus_data

with open("data/weapons_properties.json") as json_data:
    weap_prop_data = json.load(json_data)
    logger.debug(weap_prop_data)
    #print weap_prop_data

if __name__ == '__main__':
    test_force_roll(100)

