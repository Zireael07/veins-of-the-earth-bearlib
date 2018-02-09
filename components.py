from bearlibterminal import terminal as blt
import libtcodpy as libtcod
import math

from renderer import draw_iso, draw_blood_splatter, draw_shield, draw_floating_text
from gui_menus import dialogue_window
from tile_lookups import get_block_path
import calendar

from generators import roll

# import constants

# need a reference to global GAME %^$@
def initialize_game(game):
    global GAME
    GAME = game

def map_check_for_creature(x, y, exclude_entity = None):

    target = None

    # find entity that isn't excluded
    if exclude_entity:
        for ent in GAME.level.current_entities:
            if (ent is not exclude_entity
                and ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

            if target:
                return target

    # find any entity if no exclusions
    else:
        for ent in GAME.level.current_entities:
            if (ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

            if target:
                return target

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

    def draw(self, fov_map, render_pos):
        is_visible = libtcod.map_is_in_fov(fov_map, self.x, self.y)

        self.visible = is_visible

        draw_item = self.item and GAME.level.current_explored[self.x][self.y]


        if self.visible or draw_item:
            tile_x, tile_y = draw_iso(self.x,self.y, render_pos) #this is the top(?) corner of our tile
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

            #cartesian
            #blt.put_ext(self.x*constants.TILE_WIDTH, self.y*constants.TILE_HEIGHT, 10, 10, self.char)

    def send_to_back(self):
        GAME.level.current_entities.remove(self)
        GAME.level.current_entities.insert(0, self)


class com_Creature(object):
    ''' Name_instance is the name of an individual, e.g. "Agrk"'''
    def __init__(self, name_instance,
                 num_dice = 1, damage_dice = 6, base_def = 0, hp=10,
                 base_str = 8, base_dex = 8, base_con = 8, base_int = 8, base_wis = 8, base_cha = 8,
                 dodge=25, melee=55,
                 faction = "enemy",
                 player = None,
                 text = None,
                 chat = None,
                 death_function=None,
                 effects=None):
        self.name_instance = name_instance
        self.max_hp = hp
        self.hp = hp
        self.num_dice = num_dice
        self.damage_dice = damage_dice
        self.base_def = base_def
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

        # player
        self.player = player
        if self.player:
            player.owner = self

        self.faction = faction
        self.text = text
        self.chat = chat
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

        if self.owner.container:
            # get weapon
            weapon = self.get_weapon()

            # get weapon dice
            if weapon is not None:
                damage_str = "Weapon " + str(weapon.equipment.num_dice)+"d"+str(weapon.equipment.damage_dice)
            else:
                damage_str = str(self.num_dice)+"d"+str(self.damage_dice)

            object_bonuses = ["Bonus " + str(obj.equipment.attack_bonus)
                              for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                damage_str.join(bonus)

        return damage_str

    @property
    def defense(self):
        total_def = self.base_def

        if self.owner.container:
            # get bonuses
            object_bonuses = [obj.equipment.defense_bonus
                              for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                total_def += bonus

        return total_def

    @property
    def defense_str(self):
        defense_str = ""
        if self.owner.container:
            # get bonuses
            object_bonuses = ["Bonus:  " + str(obj.name) + " " + str(obj.equipment.defense_bonus)
                              for obj in self.owner.container.equipped_items if obj.equipment.defense_bonus > 0]

            for bonus in object_bonuses:
                defense_str = defense_str + " " + bonus

        return defense_str

    def get_weapon(self):
        for obj in self.owner.container.equipped_items:
            if obj.equipment.attack_bonus:
                return obj
            else:
                return None

    @property
    def faction_color(self):
        return self.get_marker_color()

    def get_marker_color(self):
        react = GAME.get_faction_reaction(self.faction, "player", False)
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

    def skill_test(self, skill):
        if self.owner.visible:
            GAME.game_message("Making a test for " + skill + " target: " + str(getattr(self, skill)), "green")
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
                    GAME.game_message("You gain " + str(gain) + " skill points!", "light green")
                else:
                    # +1 if we didn't
                    setattr(self, skill, getattr(self, skill) + 1)
                    GAME.game_message("You gain 1 skill point", "light green")
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
                    GAME.game_message("You learn from your failure and gain 1 skill point", "light green")

            return False

    def attack(self, target, damage):

        if self.skill_test("melee"):
            if self.owner.visible:
                GAME.game_message(self.name_instance + " hits " + target.creature.name_instance +"!", "white")
            # assume target can try to dodge (i.e. not sleeping)
            if (target.creature.player is not None and not target.creature.player.resting) and target.creature.skill_test("dodge"):
                if self.owner.visible:
                    GAME.game_message(target.creature.name_instance + " dodges!", "green")
            else:
                if self.owner.visible:
                    GAME.game_message(self.name_instance + " deals " + str(damage) + " damage to " + target.creature.name_instance, "red")
                target.creature.take_damage(damage)
        else:
            if self.owner.visible:
                tile_x, tile_y = draw_iso(target.x, target.y, GAME.level.render_positions)
                draw_shield(tile_x, tile_y)
                GAME.game_message(self.name_instance + " misses " + target.creature.name_instance + "!", "lighter blue")

    def take_damage(self, damage):
        change = damage - self.defense
        if change < 0:
            change = 0
        self.hp -= change
        if self.owner.visible:
            if self.defense > 0:
                GAME.game_message(self.name_instance + " blocks " + str(self.defense) + " damage", "gray")
            tile_x, tile_y = draw_iso(self.owner.x, self.owner.y, GAME.level.render_positions)
            draw_blood_splatter(tile_x, tile_y, change)
            GAME.game_message(self.name_instance + "'s hp is " + str(self.hp) + "/" + str(self.max_hp), "white")

        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def heal(self, amount):
        self.hp += amount
        if self.owner.visible:
            GAME.game_message(self.name_instance + " heals!", "lighter red")

    def move(self, dx, dy, game_map):
        if self.owner.y + dy >= len(game_map) or self.owner.y + dy < 0:
            print("Tried to move out of map")
            return

        if self.owner.x + dx >= len(game_map[0]) or self.owner.x + dx < 0:
            print("Tried to move out of map")
            return

        target = None

        target = map_check_for_creature(self.owner.x + dx, self.owner.y + dy, self.owner)


        if target and target.creature.faction != self.faction:

            is_enemy_faction = GAME.get_faction_reaction(self.faction, target.creature.faction, False) < 0

            if is_enemy_faction:
                #print "Target faction " + target.creature.faction + " is enemy!"
                damage_dealt = self.damage
                self.attack(target, damage_dealt)
            else:
                if self.text is not None and self.owner.visible:
                    tile_x, tile_y = draw_iso(self.owner.x, self.owner.y, GAME.level.render_positions)
                    draw_floating_text(tile_x, tile_y-1, self.text)
                    #draw_floating_text_step(tile_x, tile_y-1, self.text)
                    GAME.game_message(self.name_instance + " says: " + self.text, "yellow")
                if target.creature.text is not None and target.visible:
                    tile_x, tile_y = draw_iso(target.x, target.y, GAME.level.render_positions)
                    draw_floating_text(tile_x, tile_y - 1, target.creature.text)
                    # draw_floating_text_step(tile_x, tile_y-1, target.creature.text)
                    GAME.game_message(target.creature.name_instance + " says: " + target.creature.text, "yellow")

                # test
                if self.chat is not None:
                    dialogue_window(self)
                    # wake player if he's sleeping
                    if target.creature.player.resting:
                        target.creature.player.resting = False

                if target.creature.chat is not None:
                    dialogue_window(target.creature)

        tile_is_wall = (get_block_path(game_map[self.owner.x+dx][self.owner.y+dy]) == True)

        if not tile_is_wall and target is None:
            self.owner.x += dx
            self.owner.y += dy

            #flag so that we don't recalculate FOV/camera needlessly
            return True

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
        return self.move(dx, dy, game_map)


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
    def __init__(self, weight=0.0, use_function=None):
        self.weight = weight
        self.use_function = use_function

    def pick_up(self, actor):
        if actor.container:
            actor.container.inventory.append(self.owner)
            self.current_container = actor.container
            # special case: we might not be in the entities list at all if creating NPC inventory
            if self.owner in GAME.level.current_entities:
                GAME.level.current_entities.remove(self.owner)
                # if we're creating NPC inventory, don't make a log message
                GAME.game_message(actor.creature.name_instance + " picked up " + self.owner.name, "white")

    def drop(self, actor):
        GAME.game_message(actor.creature.name_instance + " dropped " + self.owner.name, "white")
        self.current_container.inventory.remove(self.owner)

        GAME.level.current_entities.append(self.owner)
        self.owner.send_to_back()

        self.owner.x = actor.x
        self.owner.y = actor.y

    def use(self, actor):
        if self.owner.equipment:
            self.owner.equipment.toggle_equip(actor)
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
        GAME.game_message(actor.creature.name_instance + " equipped " + self.owner.name, "white")

    def unequip(self, actor):
        self.equipped = False
        GAME.game_message(actor.creature.name_instance + " took off " + self.owner.name, "white")


class Effect(object):
    def __init__(self, name, color="green", duration=1,strength=0):
        self.name = name
        self.color = color
        self.duration = duration
        self.strength_bonus = strength

    def apply_effect(self, target):
        GAME.game_message(target.name_instance + " is now affected by " + str(self.name), self.color)

        target.effects.append(self)
        self.owner = target

    def remove_effect(self):
        self.owner.effects.remove(self)
        GAME.game_message(self.owner.name_instance + " is no longer affected by " + str(self.name), self.color)

    def countdown(self):
        self.duration -= 1
        if self.duration <= 0:
            self.remove_effect()

class com_Player(object):
    def __init__(self):
        self.resting = False
        self.rest_cnt = 0
        self.rest_turns = 0
        self.nutrition = 500
        self.thirst = 300

    def act(self):
        if self.resting:
            self.resting_step()

        # count down nutrition/thirst
        # halve hunger rate when sleeping
        if self.resting:
            self.nutrition -= 0.5
            self.thirst -= 0.5
        else:
            self.nutrition -= 1
            self.thirst -= 1

        # general stuff
        # count down effects
        for ef in self.owner.effects:
            ef.countdown()

    def rest_start(self, turns):
        self.rest_cnt = 0
        self.resting = True
        self.rest_turns = turns
        GAME.game_message("Resting starts...", "blue")

        if self.resting and self.rest_cnt >= turns:
            self.rest_stop()
        else:
            # toggle game state to enemy turn
            GAME.end_player_turn()
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
                heal = ((1+3)*self.owner.constitution)/5

                self.owner.hp = int(min(self.owner.max_hp, self.owner.hp+heal))


            # toggle game state to enemy turn
            GAME.end_player_turn()
            self.rest_cnt += 1

    def rest_stop(self):
        self.resting = False
        # passage of time
        GAME.calendar.turn += calendar.HOUR*8
        GAME.game_message("Rested for " + str(self.rest_cnt) + " turns", "blue")
        GAME.game_message(GAME.calendar.get_time_date(GAME.calendar.turn), "blue")
