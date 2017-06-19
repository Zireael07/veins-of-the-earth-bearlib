# coding: utf8

from bearlibterminal import terminal as blt
import constants



class struc_Tile:
    def __init__(self, block_path):
        self.block_path = block_path

def map_create():
    new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]

    new_map[10][10].block_path = True
    new_map[12][12].block_path = True

    return new_map

def draw_game():
    global GAME_MAP
    # blt.printf(1, 1, 'Hello, world!')

    draw_map(GAME_MAP)

    # blt.refresh()

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
        key = blt.read()
        if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
            game_quit = True

        # draw
        draw_game()

        # refresh term
        blt.refresh()

    # quit the game
    blt.close()


def game_initialize():
    global GAME_MAP

    blt.open()
    blt.set("window: size=80x25, cellsize=auto, title='Veins of the Earth'; font: default")

    # needed to avoid insta-close
    blt.refresh()

    #tiles
    blt.set("0x02E: gfx/floor_sand.png")
    blt.set("0x23: gfx/wall_stone.png")

    GAME_MAP = map_create()

if __name__ == '__main__':
    game_initialize()
    game_main_loop()


