# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod
from time import time

import constants
import renderer
import components
import generators

class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path
        self.explored = False

class obj_Game:
    def __init__(self):
        self.current_map = map_create()
        self.current_entities = []
        self.factions = []

        self.message_history = []

    def game_message(self, msg, msg_color):
        self.message_history.append((msg, msg_color))

    def add_entity(self, entity):
        if entity is not None:
            self.current_entities.append(entity)

    def add_faction(self, faction_data):
        self.factions.append(faction_data)
        print "Added faction " + str(faction_data)
        # add the reverse mapping, too
        self.factions.append((faction_data[1], faction_data[0], faction_data[2]))
        print "Added reverse faction " + str((faction_data[1], faction_data[0], faction_data[2]))

    def get_faction_reaction(self, faction, target_faction, log):
        if faction == target_faction:
            return 100


        for fact in self.factions:
            if fact[0] == faction and fact[1] == target_faction:
                if log:
                    print("Faction reaction of " + fact[0] + " to " + fact[1] + " is " + str(fact[2]))
                return fact[2]


class AI_test:
    def take_turn(self):
        self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1), GAME.current_map)


class Rect():
    """
    A rectangle on the map. used to characterize a room.
    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + max(0, w)
        self.y2 = y + max(0, h)

    def __eq__(self, other):
        return (self.x1 == other.x1 and
                self.x2 == other.x2 and
                self.y1 == other.y1 and
                self.y2 == other.y2)

    def center(self):
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    def intersect(self, other):
        """
        Returns true if two rectangles intersect.
        """
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

    def contains(self, location):
        return (location[0] > self.x1 and location[0] <= self.x2 and
                self.y1 < location[1] <= self.y2)


class obj_Camera:
    def __init__(self):
        self.width = 80 # blt.state(blt.TK_CELL_WIDTH)*80
        self.height = 25 # blt.state(blt.TK_CELL_HEIGHT)*25
        self.x, self.y = (0,0)
        self.top_x, self.top_y = (0,0)
        self.offset = (0,10) #default offset is 10 along y axis
    
    def update(self):
        # this calculates cells
        self.x, self.y = renderer.draw_iso(PLAYER.x, PLAYER.y)
        self.top_x, self.top_y = self.x - self.width/2, self.y - self.height/2

    @property
    def rectangle(self):
        cam_rect = Rect(self.top_x, self.top_y, self.width, self.height)
        return cam_rect


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
    draw_x, draw_y = renderer.draw_iso(tile_x, tile_y)

    blt.color("light yellow")
    blt.put(draw_x, draw_y, 0x2317)


def cell_to_iso(x,y):
    offset_x = constants.MAP_WIDTH * 4
    iso_x = y / constants.TILE_HEIGHT + (x - offset_x) / constants.TILE_WIDTH
    iso_y = y / constants.TILE_HEIGHT - (x - offset_x) / constants.TILE_WIDTH - CAMERA.offset[1]
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
        # fake an offset of camera offset * cell height
        pix_y = pix_y - CAMERA.offset[1]*blt.state(blt.TK_CELL_HEIGHT)

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


        # camera
        CAMERA.update()

        # draw
        draw_game(pix_x, pix_y)

        # debug
        blt.puts(2,2, "[color=red] player pos in cells: %d %d" % (renderer.draw_iso(PLAYER.x, PLAYER.y)))
        blt.puts(2,6, "[color=orange] camera pos in cells: %d %d" % (CAMERA.x, CAMERA.y))


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

        # fake an offset of camera offset * cell height
        pix_y = pix_y - CAMERA.offset[1] * blt.state(blt.TK_CELL_HEIGHT)

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


def game_initialize():
    global GAME, FOV_CALCULATE, PLAYER, CAMERA

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
    blt.set("0x2017: gfx/unit_marker.png, align=center") # "̳"

    GAME = obj_Game()

    FOV_CALCULATE = True

    # init game for submodules
    components.initialize_game(GAME)
    generators.initialize_game(GAME)

    # init factions
    GAME.add_faction(("player", "enemy", -100))
    GAME.add_faction(("player", "neutral", 0))

    container_com1 = components.com_Container()
    player_array = generators.generate_stats("heroic")
    creature_com1 = components.com_Creature("Player",
                                            base_str=player_array[0], base_dex=player_array[1], base_con=player_array[2],
                                            base_int=player_array[3], base_wis=player_array[4], base_cha=player_array[5],
                                            faction="player")

    PLAYER = components.obj_Actor(1,1, "@", "Player", creature=creature_com1, container=container_com1)
    
    CAMERA = obj_Camera()

    #init camera for renderer
    renderer.initialize_camera(CAMERA)
    

    #test generating items
    GAME.current_entities.append(generators.generate_item(2, 2, "longsword"))
    GAME.current_entities.append(generators.generate_item(3,3, "dagger"))
    GAME.current_entities.append(generators.generate_item(1,1, "chainmail"))

    GAME.add_entity(generators.generate_monster(2,2, "human"))
    #test generating monsters
    GAME.add_entity(generators.generate_monster(3, 3, generators.generate_random_mon()))
    GAME.add_entity(generators.generate_monster(5, 5, generators.generate_random_mon()))
    GAME.add_entity(generators.generate_monster(7, 7, generators.generate_random_mon()))
    GAME.add_entity(generators.generate_monster(4, 4, generators.generate_random_mon()))
    GAME.add_entity(generators.generate_monster(8, 8, generators.generate_random_mon()))
    GAME.add_entity(generators.generate_monster(10, 10, generators.generate_random_mon()))
    GAME.add_entity(generators.generate_monster(15, 15, generators.generate_random_mon()))

    # put player last
    GAME.current_entities.append(PLAYER)

    #test
    generators.get_random_item()

if __name__ == '__main__':

    game_initialize()
    game_main_loop()


