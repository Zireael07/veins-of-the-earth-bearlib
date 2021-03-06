# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod
import math
from timeit import default_timer
import random

from map_common import map_check_for_creature, direction_to, find_free_grid_in_range
from renderer import draw_iso, draw_floating_text, draw_iso_offset
from gui_menus import dialogue_window
from tile_lookups import get_block_path
import calendar
import events

from generators import roll, generate_item

import constants
import game_vars
from equipment_slots import EquipmentSlots

STAT_NAME_TO_PROP = {
        "DEX": "dexterity",
        "CON": "constitution",
        "INT": "intelligence"
}


# returns the equipment in a slot, or None if it's empty
def get_equipped_in_slot(actor, slot):
    for obj in actor.container.inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.equipped:
            return obj.equipment
    return None


class obj_Actor(object):
    ''' Name is the name of the whole class, e.g. "goblin"'''
    def __init__(self, x, y, char, name, creature=None, ai=None, container=None, item=None, equipment=None):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.creature = creature
        self.visible = False

        if self.creature:
            creature.owner = self
            # set race
            creature.race = self.name

        self.ai = ai
        if self.ai:
            ai.owner = self

        self.container = container
        if self.container:
            container.owner = self

        self.item = item
        if self.item:
            item.owner = self

        self.equipment = equipment
        if self.equipment:
            equipment.owner = self

    def display_name(self):
        if self.creature:
            return (self.creature.name_instance + " the " + self.name)

        if self.item:
            if self.equipment and self.equipment.equipped:
                return self.name + " (equipped in slot: " + self.equipment.slot + ")"
            else:
                return self.name

    def draw(self, fov_map, offset):
        #is_visible = libtcod.map_is_in_fov(fov_map, self.x, self.y)
        is_visible = fov_map.lit(self.x,self.y)

        self.visible = is_visible or constants.DEBUG

        draw_item = self.item and game_vars.level.current_explored[self.x][self.y]


        if self.visible or draw_item:
            tile_x, tile_y = draw_iso_offset(self.x,self.y, constants.RENDER_POSITIONS, offset) #this is the top(?) corner of our tile
            # this works for ASCII mode
            #blt.put_ext(tile_x, tile_y, 0, blt.state(blt.TK_CELL_HEIGHT), self.char)

            # draw the marker
            if self.creature and self.creature.faction:
                blt.color(self.creature.faction_color)
                #blt.color(self.creature.get_marker_color())
                blt.put_ext(tile_x, tile_y, 0, 0, 0x2017)
                #blt.color("white")
                blt.color(4294967295)

            #draw our tile
            blt.put_ext(tile_x, tile_y, 0, 2, self.char)

            if self.creature and self.creature.player:
                # paperdoll
                for obj in self.container.equipped_items:
                    if hasattr(obj.item, 'paperdoll'):
                        blt.put_ext(tile_x, tile_y, 0, 2, obj.item.paperdoll)

            #cartesian
            #blt.put_ext(self.x*constants.TILE_WIDTH, self.y*constants.TILE_HEIGHT, 10, 10, self.char)

    def draw_label(self):
        draw_item = self.item and game_vars.level.current_explored[self.x][self.y]

        if self.visible or draw_item:
            tile_x, tile_y = draw_iso(self.x, self.y, constants.RENDER_POSITIONS)
            blt.color(4294967295)
            blt.layer(4)
            blt.puts(tile_x-int(len(self.name)/2), tile_y-2, self.name)
            blt.layer(0)

    def send_to_back(self):
        game_vars.level.current_entities.remove(self)
        game_vars.level.current_entities.insert(0, self)


class com_Creature(object):
    ''' Name_instance is the name of an individual, e.g. "Agrk"'''
    def __init__(self, name_instance,
                 num_dice = 1, damage_dice = 6, base_def = 0, hp=10,
                 base_str = 8, base_dex = 8, base_con = 8, base_int = 8, base_wis = 8, base_cha = 8,
                 dodge=25, melee=55,
                 gender = "male",
                 faction = "enemy",
                 player = None,
                 text = None,
                 chat = None,
                 languages = None,
                 death_function=None,
                 effects=None):
        self.name_instance = name_instance
        self.max_hp = hp
        self.hp = hp
        self.num_dice = num_dice
        self.damage_dice = damage_dice
        self.base_def = base_def
        # body parts
        self.body_parts = []
        # the 6 stats
        self.base_str = base_str
        self.base_dex = base_dex
        self.base_con = base_con
        self.base_int = base_int
        self.base_wis = base_wis
        self.base_cha = base_cha
        # skills
        self.dodge = dodge
        self.melee = melee
        self.gender = gender

        # pathing
        self.move_queue = []
        self.path = []
        # debug
        self.path_moves = []

        # player
        self.player = player
        if self.player:
            player.owner = self

        self.faction = faction
        self.text = text
        self.chat = chat
        if languages is None:
            self.languages = []
        else:
            self.languages = languages
        self.death_function = death_function

        if effects is None:
            effects = []
        self.effects = effects

    @property
    def strength(self):
        return self.base_str

    @strength.setter
    def strength(self, value):
        self.base_str = value

    @property
    def dexterity(self):
        return self.base_dex

    @dexterity.setter
    def dexterity(self, value):
        self.base_dex = value

    @property
    def constitution(self):
        return self.base_con

    @constitution.setter
    def constitution(self, value):
        self.base_con = value

    @property
    def intelligence(self):
        return self.base_int

    @intelligence.setter
    def intelligence(self, value):
        self.base_int = value

    @property
    def wisdom(self):
        return self.base_wis

    @wisdom.setter
    def wisdom(self, value):
        self.base_wis = value

    @property
    def charisma(self):
        return self.base_cha

    @charisma.setter
    def charisma(self, value):
        self.base_cha = value

    @property
    def damage(self):
        total_damage = 0 #self.base_atk

        if self.owner.container:

            # get weapon
            weapon = self.get_weapon()

            # get weapon dice
            if weapon is not None:
                total_damage = roll(weapon.equipment.num_dice, weapon.equipment.damage_dice)
            else:
                total_damage = roll(self.num_dice, self.damage_dice)

            #print self.name_instance + ": Total damage after rolling is " + str(total_damage)

            # strength bonus
            str_bonus = int(math.floor(((self.strength - 10) / 2)))
            print("STR bonus: " + str(str_bonus))
            total_damage += str_bonus


            # get bonuses
            object_bonuses = [ obj.equipment.attack_bonus
                               for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                total_damage += bonus
                # print "Adding bonus of " + str(bonus)

        # if we don't have an inventory (NPC)
        else:
            total_damage = roll(self.num_dice, self.damage_dice)
            # print self.name_instance + ": NPC total attack after rolling is " + str(total_attack)

        return total_damage

    @property
    def damage_str(self):
        damage_str = []

        if self.owner.container:
            # get weapon
            weapon = self.get_weapon()

            # get weapon dice
            if weapon is not None:
                damage_str.append(["Weapon " + str(weapon.equipment.num_dice)+"d"+str(weapon.equipment.damage_dice)])
            else:
                damage_str.append([str(self.num_dice)+"d"+str(self.damage_dice)])

            # Strength bonus
            str_bonus = int(math.floor(((self.strength - 10) / 2)))
            damage_str.append(["Strength " + str(str_bonus)])


            object_bonuses = [["Bonus " + str(obj.equipment.attack_bonus)]
                              for obj in self.owner.container.equipped_items if obj.equipment.attack_bonus > 0]

            for bonus in object_bonuses:
                damage_str.append(bonus)

        return damage_str



    def get_weapon(self):
        for obj in self.owner.container.equipped_items:
            if obj.equipment.attack_bonus:
                return obj
            else:
                return None

    def get_light_radius(self):
        radius = 4
        if self.player:
            for obj in self.owner.container.equipped_items:
                if obj.name == u"torch":
                    radius = 4 #20 ft.
                    break
                else:
                    radius = 1 # getting by with touch
        else:
            radius = 4

        return radius

    @property
    def faction_color(self):
        return self.get_marker_color()

    def get_marker_color(self):
        react = game_vars.game_obj.get_faction_reaction(self.faction, "player", False)
        if react < -50:
            return "red"
        elif react < 0:
            return "orange"
        elif react == 0:
            return "yellow"
        elif react > 50:
            return "cyan"
        elif react > 0:
            return "blue"



    def set_body_parts(self, parts):
        BP_TO_HP = {
            "head": 0.33,
            "torso": 0.4,
            "arm": 0.25,
            "leg": 0.25,
        }

        #print("Setting body parts...")
        for p in parts:
            #print("Setting " + str(p))

            if p in BP_TO_HP:
                hp = int(BP_TO_HP[p]*self.max_hp)
                #print("Looking up hp.." + str(hp))
                body_part = com_BodyPart(p, hp, self.base_def)
                body_part.owner = self
                self.body_parts.append(body_part)

                # name, hp, max_hp
                #self.body_parts.append([p, hp, hp])


    def apply_stat_bonuses(self):
        import generators
        if self.owner.name in generators.races_data:
            if 'stat_bonuses' in generators.races_data[self.owner.name]:
                print(generators.races_data[self.owner.name]['stat_bonuses'])
                for b in generators.races_data[self.owner.name]['stat_bonuses']:
                    print(b)
                    print("Increasing stat " + str(STAT_NAME_TO_PROP[b[0]]) + " by " + str(b[1]))
                    setattr(self, STAT_NAME_TO_PROP[b[0]], getattr(self, STAT_NAME_TO_PROP[b[0]]) + b[1])

    def display_stat_bonus(self, stat):
        import generators
        ret = None

        if self.owner.name in generators.races_data:
            if 'stat_bonuses' in generators.races_data[self.owner.name]:
                print(generators.races_data[self.owner.name]['stat_bonuses'])
                for b in generators.races_data[self.owner.name]['stat_bonuses']:
                    if STAT_NAME_TO_PROP[b[0]] == stat:
                        ret = b[1]

        if ret is not None:
            return " + " + str(ret)
        else:
            return ''

    # d100 roll under
    def skill_test(self, skill):
        if self.owner.visible:
            events.notify(events.GameEvent("MESSAGE",
                                    ("Making a test for " + skill + " target: " + str(getattr(self, skill)), "green")))
        result = roll(1,100)

        if result < getattr(self, skill):
            # player only
            if self.player and not self.player.resting:
                # check how much we gain in the skill
                tick = roll(1, 100)
                # roll OVER the current skill
                if tick > getattr(self, skill):
                    # +1d4 if we succeeded
                    gain =  roll(1, 4)
                    setattr(self, skill, getattr(self, skill) + gain)
                    events.notify(events.GameEvent("MESSAGE", ("You gain " + str(gain) + " skill points!", "light green")))
                else:
                    # +1 if we didn't
                    setattr(self, skill, getattr(self, skill) + 1)
                    events.notify(events.GameEvent("MESSAGE", ("You gain 1 skill point", "light green")))
            return True
        else:
            # player only
            if self.player and not self.player.resting:
                # if we failed, the check for gain is different
                tick = roll(1,100)
                # roll OVER the current skill
                if tick > getattr(self, skill):
                    # +1 if we succeeded, else nothing
                    setattr(self, skill, getattr(self, skill) + 1)
                    events.notify(events.GameEvent("MESSAGE",
                                            ("You learn from your failure and gain 1 skill point", "light green")))

            return False

    def attack(self, target, damage, damage_details):
        if self.skill_test("melee"):
            if self.owner.visible:
                events.notify(events.GameEvent("MESSAGE",
                                            (self.name_instance + " hits " + target.creature.name_instance +"!", "white")))
            # assume target can try to dodge (i.e. not sleeping)
            if (target.creature.player is not None and not target.creature.player.resting) and target.creature.skill_test("dodge"):
                if self.owner.visible:
                    events.notify(events.GameEvent("MESSAGE", (target.creature.name_instance + " dodges!", "green")))
            else:
                if self.owner.visible:
                    events.notify(events.GameEvent("MESSAGE",
                                    (self.name_instance + " deals " + str(damage) + " damage to " + target.creature.name_instance, "red", damage_details)))
                target.creature.take_damage(damage)
        else:
            if self.owner.visible:
                shield = com_VisualEffect(target.x, target.y, owner=target)
                shield.tiles.append((0x2BC2, "white"))
                game_vars.level.current_effects.append(shield)

                events.notify(events.GameEvent("MESSAGE",
                                        (self.name_instance + " misses " + target.creature.name_instance + "!", "lighter blue")))


    def random_body_part(self):
        loc = roll(1,20)
        if loc < 3:
            return self.body_parts[4] # left "leg"
        elif loc < 6:
            return self.body_parts[5] # right leg
        elif loc < 13:
            return self.body_parts[1] # torso
        elif loc < 16:
            return self.body_parts[2] # left arm
        elif loc < 19:
            return self.body_parts[3] # right arm
        else:
            return self.body_parts[0] # head

    def injured_body_parts(self):
        injured = []
        for p in self.body_parts:
            if p.hp < p.max_hp:
                injured.append(self.body_parts.index(p))

        return injured

    def take_damage(self, damage, bypass=False):
        '''

        :param damage: damage taken
        :param bypass: do we apply defense? (not the case for starvation)
        :return:
        '''
        # determine body part hit
        part = self.random_body_part()
        if not bypass:
            change = damage - part.defense #self.defense
            print("Defense: " + str(part.defense))
        else:
            change = damage
        if change < 0:
            change = 0
        #self.hp -= change
        part.hp -= change

        if self.owner.visible:
            if not bypass:
                #if self.defense > 0:
                if part.defense > 0:
                    events.notify(events.GameEvent("MESSAGE",
                                                (self.name_instance + " blocks " + str(part.defense) + " damage", "gray")))

                splatter = com_VisualEffect(self.owner.x, self.owner.y, owner=self.owner)
                splatter.tiles.append((0x2BC1, "red"))
                for l in str(damage):
                    splatter.tiles.append((l, "white"))

                game_vars.level.current_effects.append(splatter)

                events.notify(events.GameEvent("MESSAGE",
                                    (self.name_instance + "'s " + str(part.name) + " hp is " + str(part.hp) + "/" + str(part.max_hp), "white")))

                # wake player if he's sleeping
                if self.player is not None and self.player.resting:
                    print("Wake up player")
                    self.player.resting = False
                    # redraw
                    game_vars.redraw = True

            else:
                events.notify(events.GameEvent("MESSAGE", (self.name_instance + " is STARVING!", "red")))


        #if self.hp <= 0:
        if (part.name == "torso" or part.name == "head") and part.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def heal(self, amount):
        # determine injured body part hit
        injuries = self.injured_body_parts()

        if len(injuries) < 1:
            return

        part = self.body_parts[random.choice(injuries)]

        part.hp += amount

        if self.owner.visible:
            events.notify(events.GameEvent("MESSAGE", (self.name_instance + "'s " + str(part.name) + " heals!", "lighter red")))

    def speak_same_language(self, target):
        print("Creature languages: " + str(target.languages) + " player languages " + str(self.languages))

        # basically finding common element in two lists
        for l in self.languages:
            if l in target.languages:
#                print(self.name_instance + " and " + target.name_instance + " know same language")
                return True

            #print(self.name_instance + " and " + target.name_instance + " don't know same language")
            return False


    # basic movement functions
    def move(self, dx, dy, game_map):
        #if self.player:
        #    print("[Player] Moving..." + str(dx) + " " + str(dy))
        if self.owner.y + dy >= len(game_map[0]) or self.owner.y + dy < 0:
            print("Tried to move out of map")
            return

        if self.owner.x + dx >= len(game_map) or self.owner.x + dx < 0:
            print("Tried to move out of map")
            return

        target = None

        target = map_check_for_creature(self.owner.x + dx, self.owner.y + dy, self.owner)


        if target and target.creature.faction != self.faction:

            is_enemy_faction = game_vars.game_obj.get_faction_reaction(self.faction, target.creature.faction, False) < 0

            if is_enemy_faction:
                #print "Target faction " + target.creature.faction + " is enemy!"
                damage_dealt = self.damage
                damage_details = self.damage_str
                self.attack(target, damage_dealt, damage_details)
            else:
                if self.text is not None and self.owner.visible and target.creature.player:
                    tile_x, tile_y = draw_iso(self.owner.x, self.owner.y, constants.RENDER_POSITIONS)
                    draw_floating_text(tile_x, tile_y-1, self.text)
                    #draw_floating_text_step(tile_x, tile_y-1, self.text)
                    events.notify(events.GameEvent("MESSAGE", (self.name_instance + " says: " + self.text, "yellow")))

                    # wake player if he's sleeping
                    if target.creature.player is not None and target.creature.player.resting:
                        target.creature.player.resting = False
                        # redraw
                        game_vars.redraw = True

                if target.creature.text is not None and target.visible and self.player:
                    tile_x, tile_y = draw_iso(target.x, target.y, constants.RENDER_POSITIONS)
                    draw_floating_text(tile_x, tile_y - 1, target.creature.text)
                    # draw_floating_text_step(tile_x, tile_y-1, target.creature.text)
                    events.notify(events.GameEvent("MESSAGE",
                                        (target.creature.name_instance + " says: " + target.creature.text, "yellow")))

                # test
                # if self.chat is not None:
                #     items = []
                #     item = GAME.level.spawn_item_by_id("chainmail")
                #     items.append(item)
                #
                #
                #     dialogue_window(self, target.creature, items)
                #     # wake player if he's sleeping
                #     if target.creature.player.resting:
                #         target.creature.player.resting = False

                # player initiated conversations
                if target.creature.chat is not None and self.player:
                    items = []

                    item = generate_item("chainmail", target.x, target.y)
                    #item = game_vars.level.spawn_item_by_id("chainmail")
                    # remove from level immediately
                    #game_vars.level.current_entities.remove(item)

                    items.append(item)

                    self.speak_same_language(target.creature)
                    dialogue_window(target.creature, self, items)

        tile_is_wall = (get_block_path(game_map[self.owner.x+dx][self.owner.y+dy]) == True)

        if not tile_is_wall and target is None:
            self.owner.x += dx
            self.owner.y += dy

            #flag so that we don't recalculate FOV/camera needlessly
            return True

    # those come from the libtcod tutorial
    def move_towards(self, target_x, target_y, game_map):
        # vector from this object to the target, and distance
        dx = target_x - self.owner.x
        dy = target_y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        return self.move(dx, dy, game_map), dx, dy

    def move_to_target(self, x, y, game_map):
        # vector from this object to the target, and distance
        dx = x - self.owner.x
        dy = y - self.owner.y
        return self.move(dx, dy, game_map), dx, dy

    # this is based on Direction constants
    def move_direction(self, direction, game_map):
        return self.move(direction[0], direction[1], game_map), direction[0], direction[1]

    # complex movement functions
    def move_towards_path_queue(self, target_x, target_y, inc_map):
        # Create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(len(inc_map), len(inc_map[0]))

        # Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(len(inc_map[0])):
            for x1 in range(len(inc_map)):
                libtcod.map_set_properties(fov, x1, y1,
                                           not get_block_path(inc_map[x1][y1]),
                                           not get_block_path(inc_map[x1][y1]))


        my_path = libtcod.path_new_using_map(fov, 1.41)
        libtcod.path_compute(my_path, self.owner.x, self.owner.y, target_x, target_y)

        # empty path
        #python_path = []
        self.path = []

        # empty queue
        self.move_queue = []
        # empty debug list
        self.path_moves = []

        if not libtcod.path_is_empty(my_path):
            # test whole path
            for i in range(libtcod.path_size(my_path)):
                x, y = libtcod.path_get(my_path, i)
                self.path.append((x,y))
                #python_path.append((x,y))

            # we can't use libtcod.path_get(my_path, i+1) because, well... it crashes
            #for i in range(len(python_path)-1):
            for i in range(len(self.path)-1):
                x,y = self.path[i]
                x1, y1 = self.path[i+1]

                #x, y = python_path[i]
                #x1, y1 = python_path[i+1]
                #print("I: " + str(i) + " coord: " + str(x) + " " + str(y) + ", next coord: " + str(x1) + " " + str(y1))
                direct = direction_to((x,y), (x1, y1))
                #direct = direction_to(python_path[i], (x1, y1))
                #print(str(dir))

                self.move_queue.append(direct)

            # debug
            self.path_moves = zip(self.path, self.move_queue)

            # append direction from our position to 0
            direct = direction_to((self.owner.x, self.owner.y), self.path[0])  # python_path[0])
            #print("First dir " + str(direct))
            self.move_queue.insert(0, direct)
            self.path_moves.insert(0, ((self.owner.x, self.owner.y), direct))
            #self.move_queue.append(direct)

        else:
            print("Path is empty! No path")
            # x, y = libtcod.path_walk(my_path, True)
            # if x or y:
            #     # Move to next path
            #     return self.owner.move_towards(x, y, inc_map)
        libtcod.path_delete(my_path)

    def moves_from_queue(self):
        if len(self.move_queue) > 1:
            #print("Move queue:" + str(self.move_queue))
            # so that we can remove
            sel_move = list(self.move_queue)
            for i in range(len(sel_move)):
                m = sel_move[i]
                # move in indicated direction
                print("Move from queue: " + str(m))
                moved = self.move_direction(m, game_vars.level.current_map)
                if moved:
                    # remove
                    self.move_queue.remove(m)

                return moved

        else:
            print("No moves in queue!")
            return


BP_TO_SLOT = {
    "torso": EquipmentSlots.BODY,
    "head": EquipmentSlots.HEAD,
    "leg": EquipmentSlots.LEGS,
    "arm": EquipmentSlots.OFF_HAND
}


class com_BodyPart(object):
    def __init__(self, name, hp, base_def=0):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.base_def = base_def

    @property
    def defense(self):
        total_def = self.base_def

        if self.owner.owner.container:
            # get bonuses
            #for obj in self.owner.owner.container.equipped_items:
            #    if self.name in BP_TO_SLOT:
            #        if obj.equipment.slot == str(EquipmentSlots.reverse_mapping[BP_TO_SLOT[self.name]]).to_lower():

            object_bonuses = [obj.equipment.defense_bonus
                              for obj in self.owner.owner.container.equipped_items if self.name in BP_TO_SLOT and obj.equipment.slot == str(EquipmentSlots.reverse_mapping[BP_TO_SLOT[self.name]]).lower() ]

            for bonus in object_bonuses:
                print("Bonus: " + str(bonus))
                total_def += bonus

        return total_def

    @property
    def defense_str(self):
        defense_str = ""
        if self.owner.owner.container:
            # get bonuses
            object_bonuses = ["Bonus:  " + str(obj.name) + " " + str(obj.equipment.defense_bonus)
                              for obj in self.owner.owner.container.equipped_items if self.name in BP_TO_SLOT and obj.equipment.slot == EquipmentSlots.reverse_mapping[BP_TO_SLOT[self.name]] and obj.equipment.defense_bonus > 0]

            for bonus in object_bonuses:
 #               print("Bonus: " + str(bonus))
                defense_str = defense_str + " " + bonus

        return defense_str

class com_Container(object):
    def __init__(self, inventory = None):
        if inventory is None:
            inventory = []
        self.inventory = inventory

    @property
    def equipped_items(self):
        list_equipped = [obj for obj in self.inventory
                         if obj.equipment and obj.equipment.equipped]

        return list_equipped

class com_Item(object):
    def __init__(self, price=0, weight=0.0, use_function=None):
        self.price = price
        self.weight = weight
        self.use_function = use_function

    def pick_up(self, actor):
        if actor.container:
            actor.container.inventory.append(self.owner)
            self.current_container = actor.container
            # special case: we might not be in the entities list at all if creating NPC inventory
            if self.owner in game_vars.level.current_entities:
                game_vars.level.current_entities.remove(self.owner)
                # if we're creating NPC inventory, don't make a log message
                events.notify(events.GameEvent("MESSAGE",
                                               (actor.creature.name_instance + " picked up " + self.owner.name, "white")))

    def drop(self, actor):
        events.notify(events.GameEvent("MESSAGE", (actor.creature.name_instance + " dropped " + self.owner.name, "white")))
        self.current_container.inventory.remove(self.owner)

        game_vars.level.current_entities.append(self.owner)
        self.owner.send_to_back()

        self.owner.x = actor.x
        self.owner.y = actor.y

    def use(self, actor):
        if self.owner.equipment:
            self.owner.equipment.toggle_equip(actor)
            # force recompute FOV if torch
            if self.owner.name == u"torch":
                game_vars.fov_recompute = True
            return
        elif self.use_function is not None:
            # destroy after use, unless it was cancelled for some reason
            if self.use_function(actor) != 'cancelled':
                self.current_container.inventory.remove(self.owner)

class com_Equipment(object):
    def __init__(self, slot, num_dice = 1, damage_dice = 4, attack_bonus = 0, defense_bonus = 0):
        self.slot = slot
        self.equipped = False
        self.num_dice = num_dice
        self.damage_dice = damage_dice
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus

    def toggle_equip(self, actor):
        if self.equipped:
            self.unequip(actor)
        else:
            self.equip(actor)

    def equip(self, actor):
        old_equipment = get_equipped_in_slot(actor, self.slot)
        if old_equipment is not None:
            #print "Unequipping " + old_equipment.owner.name
            old_equipment.unequip(actor)

        self.equipped = True
        events.notify(events.GameEvent("MESSAGE", (actor.creature.name_instance + " equipped " + self.owner.name, "white")))

    def unequip(self, actor):
        self.equipped = False
        events.notify(events.GameEvent("MESSAGE", (actor.creature.name_instance + " took off " + self.owner.name, "white")))


class Effect(object):
    def __init__(self, name, color="green", duration=1,strength=0):
        self.name = name
        self.color = color
        self.duration = duration
        self.strength_bonus = strength

    def apply_effect(self, target):
        events.notify(events.GameEvent("MESSAGE",
                                    (target.name_instance + " is now affected by " + str(self.name), self.color)))

        target.effects.append(self)
        self.owner = target

    def remove_effect(self):
        self.owner.effects.remove(self)
        events.notify(events.GameEvent("MESSAGE",
                                (self.owner.name_instance + " is no longer affected by " + str(self.name), self.color)))

    def countdown(self):
        self.duration -= 1
        if self.duration <= 0:
            self.remove_effect()


class com_VisualEffect(object):
    def __init__(self, x, y, duration=3, tiles=None, owner=None):
        self.x = x
        self.y = y
        if tiles is None:
            tiles = []
        self.start_time = None
        self.tiles = tiles
        self.duration = duration
        self.start_time = default_timer()
        self.render = True
        if owner:
            self.owner = owner


    def set_tiles(self, tiles):
        self.tiles = tiles

    def draw(self):
        tile_x, tile_y = draw_iso(self.x, self.y, constants.RENDER_POSITIONS)
        # changed because 3 was getting cleared too much
        blt.layer(4)
        for tile, color in self.tiles:
            blt.color(color)

            blt.put_ext(tile_x, tile_y, 0, 0, tile)

    def update(self):
        # check duration
        if default_timer() - self.start_time > self.duration:
            #print("Time to cancel..")
            self.render = False
        elif hasattr(self, 'owner') and not self.owner in game_vars.level.current_entities:
            #print("Owner dead, shorten duration")
            self.duration = 1 # so that the effects do not stay around too long if the owner is dead
        else:
            #print("Effect dur: " + str(self.duration))
            self.render = True


class com_Player(object):
    def __init__(self):
        self.resting = False
        self.rest_cnt = 0
        self.rest_turns = 0
        self.nutrition = 500
        self.thirst = 300
        self.autoexplore = False

        # not tuples because we modify the amounts during the game
        self.money = [ ["bronze", 0],
                       ["silver", 100],
                       ["gold", 0],
                       ["platinum", 0]]

        self.kids = []

    def act(self):
        if self.resting:
            #print("Resting...")
            self.resting_step()

        # count down nutrition/thirst
        # halve hunger rate when sleeping
        if self.resting:
            self.nutrition -= 0.5
            self.thirst -= 0.5
        else:
            self.nutrition -= 1
            self.thirst -= 1

        # starve/thirst
        if self.nutrition <= 0 or self.thirst <= 0:
            self.owner.take_damage(1, True)

        # general stuff
        # count down effects
        for ef in self.owner.effects:
            ef.countdown()


    # resting
    def rest_start(self, turns):
        print("Rest start...")
        self.rest_cnt = 0
        self.resting = True
        self.rest_turns = turns
        events.notify(events.GameEvent("MESSAGE", ("Resting starts...", "blue")))

        if self.resting and self.rest_cnt >= turns:
            self.rest_stop()
        else:
            import handle_input
            handle_input.fake_action("player-moved")

            # toggle game state to enemy turn
            #events.notify(events.GameEvent("END_TURN", None))
            #GAME.end_player_turn()
            self.rest_cnt += 1

    def resting_step(self):
        if not self.resting:
            return

        if self.resting and self.rest_cnt >= self.rest_turns:
            self.rest_stop()
        else:
            # actual resting stuff (actually only done once for simplicity)
            if self.rest_cnt == 6:
                # I think this formula dates back to Incursion
                healing = ((1+3)*self.owner.constitution)/5

                self.owner.heal(healing)

                #self.owner.hp = int(min(self.owner.max_hp, self.owner.hp+heal))

            import handle_input
            handle_input.fake_action("player-moved")
            # toggle game state to enemy turn
            #events.notify(events.GameEvent("END_TURN", None))
            #GAME.end_player_turn()
            self.rest_cnt += 1
            print("Rest step..." + str(self.rest_cnt))

    def rest_stop(self):
        self.resting = False
        # passage of time
        game_vars.calendar_game.turn += calendar.HOUR*8
        events.notify(events.GameEvent("MESSAGE", ("Rested for " + str(self.rest_cnt) + " turns", "blue")))
        events.notify(events.GameEvent("MESSAGE", (game_vars.calendar_game.get_time_date(game_vars.calendar_game.turn), "blue")))

        import handle_input
        handle_input.fake_action("redraw")

        # force redraw
        game_vars.redraw = True

    def city_rest(self):
        # heal
        healing = ((1 + 3) * self.owner.constitution) / 5
        self.owner.heal(healing)

        # passage of time
        game_vars.calendar_game.turn += calendar.HOUR * 8
        events.notify(events.GameEvent("MESSAGE", (
            game_vars.calendar_game.get_time_date(game_vars.calendar_game.turn), "blue")))

        # force redraw
        game_vars.redraw = True

    # money
    def add_money(self, values):
        print(str(values))
        for v in values:
            for m in self.money:
                if v[0] == m[0]:
                    m[1] += v[1]
                    print("Incrementing " + str(m[0]) + " by " + str(v[1]))
                    break

    def remove_money(self, values):
        print(str(values))
        for v in values:
            for m in self.money:
                if v[0] == m[0]:
                    m[1] -= v[1]
                    print("Decrementing " + str(m[0]) + " by " + str(v[1]))
                    break

    def check_money(self, kind, amount):
        for m in self.money:
            if m[0] == kind:
                if m[1] > amount:
                    #print("We have " + str(amount) + " of " + str(kind))
                    return True
                else:
                    #print("We don't have " + str(amount) + "of " + str(kind))
                    return False

    def generate_kid(self):
        import generators
        import ai
        container_com1 = com_Container()

        creature_com1 = com_Creature("kid", hp=10,
                                                base_str=roll(3,6), base_dex=roll(3,6),
                                                base_con=roll(3,6),
                                                base_int=roll(3,6), base_wis=roll(3,6),
                                                base_cha=roll(3,6),
                                                faction="player") #death_function=death_player)

        ai_comp = ai.NeutralAI()


        # body parts
        creature_com1.set_body_parts(generators.generate_body_types())

        # check that x,y isn't taken
        x, y = self.owner.owner.x, self.owner.owner.y
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



        kid = obj_Actor(x, y, int("0xE004", 16), "kid", creature=creature_com1, ai=ai_comp,
                                      container=container_com1)

        if kid is not None:
            game_vars.level.current_entities.append(kid)
            print("Spawned a kid " + str(kid.name))
            # append to list
            game_vars.player.creature.player.kids.append(kid)

    # TODO: figure out a better place for this
    @staticmethod
    def switch_to_kid(kid):
        print("Making the switch")
        events.notify(events.GameEvent("MESSAGE", ("Your parent is dead, " + str(kid.name) + ". It falls to you to continue his legacy", "green")))

        # remove AI
        kid.ai = None

        # switch control to kid
        player_new_com = com_Player()
        kid.creature.player = player_new_com
        player_new_com.owner = kid.creature
        import main_menu
        kid.creature.death_function = main_menu.death_player

        game_vars.player = kid
        game_vars.camera.start_update(game_vars.player)

        # force fov recompute
        game_vars.fov_recompute = True

        # force redraw
        game_vars.redraw = True