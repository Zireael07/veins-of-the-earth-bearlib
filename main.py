# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod

import constants



class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path

class obj_Actor:
    def __init__(self, x, y, char, creature=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.creature = creature

        if creature:
            creature.owner = self

        self.ai = ai
        if ai:
            ai.owner = self

    def draw(self):
        blt.put(self.x*constants.TILE_WIDTH, self.y*constants.TILE_HEIGHT, self.char)



class com_Creature:
    def __init__(self, name_instance, hp=10, death_function=None):
        self.name_instance = name_instance
        self.max_hp = hp
        self.hp = hp
        self.death_function = death_function

    def attack(self, target, damage):
        self.name_instance + " attacks " + target.creature.name_instance + " for " + str(damage) + " damage!"
        target.creature.take_damage(damage)

    def take_damage(self, damage):
        self.hp -= damage
        print self.name_instance + "'s hp is " + str(self.hp) + "/" + str(self.max_hp)

        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def move(self, dx, dy):
        if self.owner.y + dy >= len(GAME_MAP) or self.owner.y + dy < 0:
            print("Tried to move out of map")
            return

        if self.owner.x + dx >= len(GAME_MAP[0]) or self.owner.x + dx < 0:
            print("Tried to move out of map")
            return

        target = None

        target = map_check_for_creature(self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            self.attack(target, 5)

        tile_is_wall = (GAME_MAP[self.owner.x+dx][self.owner.y+dy].block_path == True)

        if not tile_is_wall and target is None:
            self.owner.x += dx
            self.owner.y += dy

class AI_test:
    def take_turn(self):
        self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1))

def death_monster(monster):
    print monster.creature.name_instance + " is dead!"
    # clean up components
    monster.creature = None
    monster.ai = None
    # remove from map
    ENTITIES.remove(monster)

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

    return new_map

def map_check_for_creature(x, y, exclude_entity = None):

    target = None

    # find entity that isn't excluded
    if exclude_entity:
        for ent in ENTITIES:
            if (ent is not exclude_entity
                and ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent

            if target:
                return target

    # find any entity if no exclusions
    else:
        for ent in ENTITIES:
            if (ent.x == x
                and ent.y == y
                and ent.creature):
                target = ent


def draw_game():
    global GAME_MAP
    # blt.printf(1, 1, 'Hello, world!')

    draw_map(GAME_MAP)

    for ent in ENTITIES:
        ent.draw()

def draw_map(map_draw):
    for x in range(0, constants.MAP_WIDTH):
        for y in range(0, constants.MAP_HEIGHT):
            if map_draw[x][y].block_path == True:
                # draw wall
                blt.put(x*constants.TILE_WIDTH,y*constants.TILE_HEIGHT, "#")
            else:
                # draw floor
                blt.put(x*constants.TILE_WIDTH,y*constants.TILE_HEIGHT, ".")


def game_main_loop():
    game_quit = False

    while not game_quit:

        #clear
        blt.clear()

        player_action = game_handle_keys()

        if player_action == "QUIT":
            game_quit = True

        if player_action != "no-action":
            for ent in ENTITIES:
                if ent.ai:
                    ent.ai.take_turn()

        # draw
        draw_game()

        # refresh term
        blt.refresh()

    # quit the game
    blt.close()

def game_handle_keys():
    key = blt.read()
    if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
        return "QUIT"

    if key == blt.TK_UP:
        PLAYER.creature.move(0, -1)
        return "player-moved"
    if key == blt.TK_DOWN:
        PLAYER.creature.move(0, 1)
        return "player-moved"
    if key == blt.TK_LEFT:
        PLAYER.creature.move(-1, 0)
        return "player-moved"
    if key == blt.TK_RIGHT:
        PLAYER.creature.move(1, 0)
        return "player-moved"


    return "no-action"

def game_initialize():
    global GAME_MAP, PLAYER, ENEMY, ENTITIES

    blt.open()
    # default terminal size is 80x25
    blt.set("window: size=80x45, cellsize=auto, title='Veins of the Earth'; font: default")

    blt.composition(True)

    # needed to avoid insta-close
    blt.refresh()

    #tiles
    blt.set("0x02E: gfx/floor_sand.png") # "."
    blt.set("0x23: gfx/wall_stone.png") # "#"
    blt.set("0x40: gfx/human_m.png") # "@"
    blt.set("0x6B: gfx/kobold.png") # "k"

    GAME_MAP = map_create()

    creature_com1 = com_Creature("Player")
    PLAYER = obj_Actor(1,1, "@", creature=creature_com1)

    creature_com2 = com_Creature("kobold", death_function=death_monster)
    ai_com = AI_test()
    ENEMY = obj_Actor(3,3, "k", creature=creature_com2, ai=ai_com)

    ENTITIES = [PLAYER, ENEMY]

if __name__ == '__main__':
    game_initialize()
    game_main_loop()


