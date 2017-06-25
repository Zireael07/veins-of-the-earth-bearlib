# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod
from time import time
import math

import constants



class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False

class obj_Game:
    def __init__(self):
        self.current_map = map_create()
        self.current_entities = []

        self.message_history = []


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

    def draw(self):
        is_visible = libtcod.map_is_in_fov(FOV_MAP, self.x, self.y)

        if is_visible:
            tile_x, tile_y = draw_iso(self.x,self.y) #this is the top(?) corner of our tile
            # this works for ASCII mode
            #blt.put_ext(tile_x, tile_y, 0, blt.state(blt.TK_CELL_HEIGHT), self.char)

            blt.put_ext(tile_x, tile_y, 0, 2, self.char)

            #cartesian
            #blt.put_ext(self.x*constants.TILE_WIDTH, self.y*constants.TILE_HEIGHT, 10, 10, self.char)


class com_Creature:
    ''' Name_instance is the name of an individual, e.g. "Agrk"'''
    def __init__(self, name_instance, base_atk = 3, base_def = 0, hp=10, death_function=None):
        self.name_instance = name_instance
        self.max_hp = hp
        self.hp = hp
        self.base_atk = base_atk
        self.base_def = base_def
        self.death_function = death_function

    @property
    def attack_mod(self):
        total_attack = self.base_atk

        if self.owner.container:
            object_bonuses = [ obj.equipment.attack_bonus
                               for obj in self.owner.container.equipped_items]

            for bonus in object_bonuses:
                total_attack += bonus

        return total_attack

    def defense(self):
        total_def = self.base_def
        return total_def

    def attack(self, target, damage):
        damage_dealt = self.attack_mod

        game_message(self.name_instance + " attacks " + target.creature.name_instance + " for " +
                     str(damage_dealt) +
                     #str(damage) +
                     " damage!", "red")
        target.creature.take_damage(damage)

    def take_damage(self, damage):
        self.hp -= damage
        game_message(self.name_instance + "'s hp is " + str(self.hp) + "/" + str(self.max_hp), "white")

        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def move(self, dx, dy):
        if self.owner.y + dy >= len(GAME.current_map) or self.owner.y + dy < 0:
            print("Tried to move out of map")
            return

        if self.owner.x + dx >= len(GAME.current_map[0]) or self.owner.x + dx < 0:
            print("Tried to move out of map")
            return

        target = None

        target = map_check_for_creature(self.owner.x + dx, self.owner.y + dy, self.owner)

        if target:
            self.attack(target, 5)

        tile_is_wall = (GAME.current_map[self.owner.x+dx][self.owner.y+dy].block_path == True)

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
            game_message("Picking up", "white")
            actor.container.inventory.append(self.owner)
            self.current_container = actor.container
            GAME.current_entities.remove(self.owner)

    def drop(self, new_x, new_y):
        game_message("Item dropped", "white")
        self.current_container.inventory.remove(self.owner)
        GAME.current_entities.append(self.owner)
        self.owner.x = new_x
        self.owner.y = new_y

    def use(self):
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return


class com_Equipment:
    def __init__(self, slot, attack_bonus = 0, defense_bonus = 0):
        self.slot = slot
        self.equipped = False
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus

    def toggle_equip(self):
        if self.equipped:
            self.unequip()
        else:
            self.equip()

    def equip(self):
        self.equipped = True

        game_message("Item equipped", "white")

    def unequip(self):
        self.equipped = False
        game_message("Took off item", "white")


class AI_test:
    def take_turn(self):
        self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1))

def death_monster(monster):
    game_message(monster.creature.name_instance + " is dead!", "gray")
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


def map_check_for_item(x,y):
    target = None

    for ent in GAME.current_entities:
        if (ent.x == x
            and ent.y == y
            and ent.item):
            target = ent

        if target:
            return target


def draw_game(x,y):
    draw_map(GAME.current_map)

    draw_mouseover(x,y)

    blt.color("white")
    for ent in GAME.current_entities:
        ent.draw()

    draw_messages()


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


def draw_map(map_draw):
    for x in range(0, constants.MAP_WIDTH):
        for y in range(0, constants.MAP_HEIGHT):

            is_visible = libtcod.map_is_in_fov(FOV_MAP, x, y)

            if is_visible:
                blt.color("white")
                map_draw[x][y].explored = True
                # cartesian
                # tile_x = x*constants.TILE_WIDTH
                # tile_y = y*constants.TILE_HEIGHT

                tile_x, tile_y = draw_iso(x,y)

                if map_draw[x][y].block_path == True:
                    # draw wall
                    blt.put(tile_x, tile_y, "#")

                else:
                    # draw floor
                    blt.put(tile_x, tile_y, 0x3002)

                    blt.put(tile_x,tile_y, ".")



            elif map_draw[x][y].explored:
                blt.color("gray")
                # cartesian
                # tile_x = x * constants.TILE_WIDTH
                # tile_y = y * constants.TILE_HEIGHT

                tile_x, tile_y = draw_iso(x,y)

                if map_draw[x][y].block_path == True:
                    # draw wall
                    blt.put(tile_x,tile_y, "#")
                else:
                    # draw floor
                    blt.put(tile_x, tile_y, 0x3002)
                    blt.put(tile_x,tile_y, ".")



def draw_messages():
    if len(GAME.message_history) <= constants.NUM_MESSAGES:
        to_draw = GAME.message_history
    else:
        to_draw = GAME.message_history[-constants.NUM_MESSAGES:]

    start_y = 45 - (constants.NUM_MESSAGES)

    i = 0
    for message, color in to_draw:
        string = "[color=" + str(color) + "] " + message
        blt.puts(2, start_y+i, string)

        i += 1


# GUI
# based on https://github.com/FirstAidKitten/Roguelike-Sandbox
def create_window(x, y, w, h, title=None):
    #test
    blt.composition(False)

    last_bg = blt.state(blt.TK_BKCOLOR)
    blt.bkcolor(blt.color_from_argb(200, 0, 0, 0))
    blt.clear_area(x - 2, y - 2, w + 2, h + 2)
    blt.bkcolor(last_bg)

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

    if title is not None:
        leng = len(title)
        offset = (w + 2 - leng) // 2
        blt.puts(x + offset, y - 1, title)


def menu(header, options, width, title=None):
    global FOV_CALCULATE

    FOV_CALCULATE = True

    menu_x = int((120 - width) / 2)

    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    header_height = 2

    menu_h = int(header_height + 1 + 26)
    menu_y = int((50 - menu_h) / 2)

    # create a window

    create_window(menu_x, menu_y, width, menu_h, title)


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
    blt.set('input: filter = [keyboard]')
    while True:
        key = blt.read()
        if blt.check(blt.TK_CHAR):
            # convert the ASCII code to an index; if it corresponds to an option, return it
            key = blt.state(blt.TK_CHAR)
            index = key - ord('a')
            if 0 <= index < len(options):
                blt.set('input: filter = [keyboard, mouse+]')
                blt.composition(True)
                return index
        else:
            blt.set('input: filter = [keyboard, mouse+]')
            blt.composition(True)
            return None


def inventory_menu(header):
    # show a menu with each item of the inventory as an option
    if len(PLAYER.container.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.display_name() for item in PLAYER.container.inventory]

    index = menu(header, options, 50, 'INVENTORY')

    # if an item was chosen, return it
    if index is None or len(PLAYER.container.inventory) == 0:
        return None
    return PLAYER.container.inventory[index]




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
        PLAYER.creature.move(0, -1)
        FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_DOWN:
        PLAYER.creature.move(0, 1)
        FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_LEFT:
        PLAYER.creature.move(-1, 0)
        FOV_CALCULATE = True
        return "player-moved"
    if key == blt.TK_RIGHT:
        PLAYER.creature.move(1, 0)
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
        chosen_item = inventory_menu("Inventory")
        if chosen_item is not None:
            if chosen_item.item:
                chosen_item.item.use()

    # mouse

    if key == blt.TK_MOUSE_LEFT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)

        click_x, click_y = pix_to_iso(pix_x, pix_y)

        print "Clicked on tile " + str(click_x) + " " + str(click_y)

        if click_x != PLAYER.x or click_y != PLAYER.y:
            PLAYER.creature.move_towards(click_x, click_y)
            FOV_CALCULATE = True

        return "player-moved"

    if  key == blt.TK_MOUSE_RIGHT:
        pix_x = blt.state(blt.TK_MOUSE_PIXEL_X)
        pix_y = blt.state(blt.TK_MOUSE_PIXEL_Y)
        print "Right clicked on tile " + str(pix_to_iso(pix_x, pix_y))

        return "mouse_click"


    return "no-action"


def game_message(msg, msg_color):
    GAME.message_history.append((msg, msg_color))

def game_initialize():
    global GAME, FOV_CALCULATE, PLAYER, ENEMY, ITEM

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
    blt.set("0xE000: gfx/kobold.png,  align=center") # ""
    blt.set("0x2317: gfx/mouseover.png, align=center") # "⌗"

    GAME = obj_Game()

    FOV_CALCULATE = True

    container_com1 = com_Container()
    creature_com1 = com_Creature("Player")
    PLAYER = obj_Actor(1,1, "@", "Player", creature=creature_com1, container=container_com1)

    creature_com2 = com_Creature("kobold", death_function=death_monster)
    ai_com = AI_test()
    # ENEMY = obj_Actor(3,3, "k", creature=creature_com2, ai=ai_com)
    ENEMY = obj_Actor(3,3, u"", "kobold", creature=creature_com2, ai=ai_com)

    equipment_com1 = com_Equipment("main_hand", attack_bonus=2)
    item_com1 = com_Item()
    ITEM = obj_Actor(2,2, "/", "sword", item=item_com1, equipment=equipment_com1)

    GAME.current_entities = [PLAYER, ENEMY, ITEM]

if __name__ == '__main__':
    game_initialize()
    game_main_loop()


