from bearlibterminal import terminal as blt
import libtcodpy as libtcod
import math

import constants

# need a reference to global GAME %^$@

def initialize_game(game):
    global GAME

    GAME = game


# based on STI library for LOVE2D
def draw_iso(x,y):
    # isometric
    offset_x = constants.MAP_WIDTH * 4
    tile_x = (x - y) * constants.TILE_WIDTH / 2 + offset_x
    tile_y = (x + y) * constants.TILE_HEIGHT / 2
    return tile_x, tile_y

def roll(dice, sides):
    result = 0
    for i in range(0, dice, 1):
        roll = libtcod.random_get_int(0, 1, sides)
        result += roll

    print 'Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result)
    return result

def map_check_for_creature(x, y, exclude_entity = None):

    target = None

    # find entity that isn't excluded
    if exclude_entity:
        for ent in GAME.current_entities:
            if (ent is not exclude_entity
                and ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

            if target:
                return target

    # find any entity if no exclusions
    else:
        for ent in GAME.current_entities:
            if (ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

class obj_Actor:
    ''' Name is the name of the whole class, e.g. "goblin"'''
    def __init__(self, x, y, char, name, creature=None, ai=None, container=None, item=None, equipment=None):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.creature = creature

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
                return self.name + " (equipped)"
            else:
                return self.name

    def draw(self, fov_map):
        is_visible = libtcod.map_is_in_fov(fov_map, self.x, self.y)

        if is_visible:
            tile_x, tile_y = draw_iso(self.x,self.y) #this is the top(?) corner of our tile
            # this works for ASCII mode
            #blt.put_ext(tile_x, tile_y, 0, blt.state(blt.TK_CELL_HEIGHT), self.char)

            blt.put_ext(tile_x, tile_y, 0, 2, self.char)

            #cartesian
            #blt.put_ext(self.x*constants.TILE_WIDTH, self.y*constants.TILE_HEIGHT, 10, 10, self.char)


class com_Creature:
    ''' Name_instance is the name of an individual, e.g. "Agrk"'''
    def __init__(self, name_instance, num_dice = 1, damage_dice = 6, base_def = 0, hp=10, death_function=None):
        self.name_instance = name_instance
        self.max_hp = hp
        self.hp = hp
        self.num_dice = num_dice
        self.damage_dice = damage_dice
        self.base_def = base_def
        self.death_function = death_function

    @property
    def attack_mod(self):
        total_attack = 0 #self.base_atk

        if self.owner.container:

            # get weapon
            weapon = self.get_weapon()

            # get weapon dice
            if weapon is not None:
                total_attack = roll(weapon.equipment.num_dice, weapon.equipment.damage_dice)
            else:
                total_attack = roll(self.num_dice, self.damage_dice)

            print self.name_instance + ": Total attack after rolling is " + str(total_attack)
            # get bonuses
            object_bonuses = [ obj.equipment.attack_bonus
                               for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                total_attack += bonus
                # print "Adding bonus of " + str(bonus)

        # if we don't have an inventory (NPC)
        else:
            total_attack = roll(self.num_dice, self.damage_dice)
            print self.name_instance + ": NPC total attack after rolling is " + str(total_attack)

        return total_attack

    def defense(self):
        total_def = self.base_def
        return total_def

    def get_weapon(self):
        for obj in self.owner.container.equipped_items:
            if obj.equipment.attack_bonus:
                return obj
            else:
                return None

    def attack(self, target, damage):

        GAME.game_message(self.name_instance + " attacks " + target.creature.name_instance + " for " +
                     str(damage) +
                     " damage!", "red")
        target.creature.take_damage(damage)

    def take_damage(self, damage):
        self.hp -= damage
        GAME.game_message(self.name_instance + "'s hp is " + str(self.hp) + "/" + str(self.max_hp), "white")

        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def move(self, dx, dy, map):
        if self.owner.y + dy >= len(map) or self.owner.y + dy < 0:
            print("Tried to move out of map")
            return

        if self.owner.x + dx >= len(map[0]) or self.owner.x + dx < 0:
            print("Tried to move out of map")
            return

        target = None

        target = map_check_for_creature(self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            damage_dealt = self.attack_mod
            self.attack(target, damage_dealt)

        tile_is_wall = (map[self.owner.x+dx][self.owner.y+dy].block_path == True)

        if not tile_is_wall and target is None:
            self.owner.x += dx
            self.owner.y += dy

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.owner.x
        dy = target_y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)


class com_Container:
    def __init__(self, inventory = []):
        self.inventory = inventory

    @property
    def equipped_items(self):
        list_equipped = [obj for obj in self.inventory
                         if obj.equipment and obj.equipment.equipped]

        return list_equipped

class com_Item:
    def __init__(self, weight=0.0):
        self.weight = weight

    def pick_up(self, actor):
        if actor.container:
            GAME.game_message("Picking up", "white")
            actor.container.inventory.append(self.owner)
            self.current_container = actor.container
            GAME.current_entities.remove(self.owner)

    def drop(self, new_x, new_y):
        GAME.game_message("Item dropped", "white")
        self.current_container.inventory.remove(self.owner)
        GAME.current_entities.append(self.owner)
        self.owner.x = new_x
        self.owner.y = new_y

    def use(self):
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return


class com_Equipment:
    def __init__(self, slot, num_dice = 1, damage_dice = 4, attack_bonus = 0, defense_bonus = 0):
        self.slot = slot
        self.equipped = False
        self.num_dice = num_dice
        self.damage_dice = damage_dice
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus

    def toggle_equip(self):
        if self.equipped:
            self.unequip()
        else:
            self.equip()

    def equip(self):
        self.equipped = True

        GAME.game_message("Item equipped", "white")

    def unequip(self):
        self.equipped = False
        GAME.game_message("Took off item", "white")