# coding: utf8
import libtcodpy as libtcod
import bisect
import json

import components
import constants

def roll(dice, sides):
    result = 0
    for i in range(0, dice, 1):
        roll = libtcod.random_get_int(0, 1, sides)
        result += roll

    print 'Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result)
    return result

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


# Execute
#if __name__ == '__main__':

# Load JSON
with open(constants.NPC_JSON_PATH) as json_data:
     monster_data = json.load(json_data)
     print monster_data

with open(constants.ITEMS_JSON_PATH) as json_data:
     items_data = json.load(json_data)
     print items_data

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

# generate_item(2, 2, "longsword")
# generate_item(3, 3, "dagger")
# generate_item(1,1, "chainmail")