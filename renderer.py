# coding: utf8

from bearlibterminal import terminal as blt
import libtcodpy as libtcod

import time
import itertools

from tile_lookups import get_char
from map_common import tiles_distance_to

import constants
import game_vars
import colors


def roll(dice, sides):
    result = 0
    for _ in range(0, dice, 1):
        roll = libtcod.random_get_int(0, 1, sides)
        result += roll

    print 'Rolling ' + str(dice) + "d" + str(sides) + " result: " + str(result)
    return result


def draw_iso(x,y,pos):
    cam = game_vars.camera

    tile_x, tile_y = pos[x][y]
    return tile_x + cam.offset[0], tile_y + cam.offset[1]

# based on STI library for LOVE2D
def draw_iso_offset(x,y, pos, offset):
    # moved to constants for precalculating
    # isometric
    # offset_x = constants.CAMERA_OFFSET
    # hw = constants.HALF_TILE_WIDTH
    # hh = constants.HALF_TILE_HEIGHT
    # tile_x = (x - y) * constants.HALF_TILE_WIDTH + offset_x
    # tile_y = (x + y) * constants.HALF_TILE_HEIGHT

    #cam = game_vars.camera

    tile_x, tile_y = pos[x][y]
    return tile_x + offset[0], tile_y + offset[1]
    #return tile_x + cam.offset[0], tile_y + cam.offset[1]

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


def draw_map(map_draw, map_explored, fov_map, debug=False):
    #width = constants.MAP_WIDTH
    #height = constants.MAP_HEIGHT
    #debug = constants.DEBUG
    cam = game_vars.camera

    width_start = cam.get_width_start()
    width_end = cam.get_width_end(map_draw)
    height_start = cam.get_height_start()
    height_end = cam.get_height_end(map_draw)
    render_pos = constants.RENDER_POSITIONS
    offset = cam.offset

    #for x in range(width_start, width_end):
    #    for y in range(height_start, height_end):
    for x,y in itertools.product(range(width_start, width_end), range(height_start, height_end)):
        if debug:
            is_visible = True
        else:
            #is_visible = libtcod.map_is_in_fov(fov_map, x, y)
            is_visible = fov_map.lit(x,y)

        if not is_visible:

            if map_explored[x][y]:
                # blt.color("gray")
                blt.color(4286545791)
                # cartesian
                # tile_x = x * constants.TILE_WIDTH
                # tile_y = y * constants.TILE_HEIGHT

                tile_x, tile_y = draw_iso_offset(x, y,render_pos, offset)

                blt.put(tile_x, tile_y, get_char(map_draw[x][y]))

        else:
            # tint light for the player
            if game_vars.player is not None and game_vars.player.creature.get_light_radius() > 1:
                #blt.color("white")
                #print(str(blt.color_from_argb(165, 255, 255, 127)))
                blt.color(dimmer(x,y, (255, 255, 127)))
            #blt.color(4294967295)
            else:
                blt.color("white")

            map_explored[x][y] = True
            # map_draw[x][y].explored = True

            # cartesian
            # tile_x = x*constants.TILE_WIDTH
            # tile_y = y*constants.TILE_HEIGHT

            tile_x, tile_y = draw_iso_offset(x, y, render_pos, offset)

            blt.put(tile_x, tile_y, get_char(map_draw[x][y]))
        #elif map_explored[x][y]:  # map_draw[x][y].explored:

dist_to_alpha = { 0: 0, 1:0, 2: 25, 3: 50, 4: 75, 5:90}

dist_to_color = { 0: colors.light_yellow, 1: colors.light_yellow, 2: colors.light_yellow_dim1, 3: colors.light_yellow_dim2,
                  4: colors.light_yellow_dim3, 5: colors.light_yellow_dim4
                  }

def dimmer(x,y, color):
    # paranoia
    #if not isinstance(color, tuple):
    #    color = (255, 255, 255)


    dist = tiles_distance_to((x, y), (game_vars.player.x, game_vars.player.y))
    #if dist in dist_to_alpha:
    if dist in dist_to_color:
        return dist_to_color[dist]
        #return blt.color_from_argb(a=255-dist_to_alpha[dist], r=color[0], g=color[1], b=color[2])
    else:
        return dist_to_color[1]
        #return blt.color_from_argb(a=255, r=color[0], g=color[1], b=color[2])


def draw_mouseover(x,y, offset):
    tile_x, tile_y = pix_to_iso(x, y)
    if 0 <= tile_x < len(game_vars.level.current_map) and 0 <= tile_y < len(game_vars.level.current_map[0]):
        draw_x, draw_y = draw_iso_offset(tile_x, tile_y, constants.RENDER_POSITIONS, offset)
        blt.color("light yellow")
        blt.put(draw_x, draw_y, 0x2317)


def draw_messages(msg_history):
    if len(msg_history) <= constants.NUM_MESSAGES:
        to_draw = msg_history
    else:
        to_draw = msg_history[-constants.NUM_MESSAGES:]

    start_y = blt.state(blt.TK_HEIGHT) - (constants.NUM_MESSAGES)

    i = 0
    for message, color, _ in to_draw:
        string = "[color=" + str(color) + "] " + message
        blt.puts(2, start_y+i, string)

        i += 1

def draw_bar(x, y, total_width, name, value, maximum, bar_color, bg_color, label=None):
    blt.color("white")
    blt.puts(x, y-1, name)

    bar_width = int(float(value) / maximum * total_width)

    for i in range(total_width):
        blt.color(bg_color)
        if i < bar_width:
            blt.color(bar_color)
        blt.put(x + i, y, 0x2588)

    if label:
        blt.color("white")
        blt.puts(x+int(total_width/2), y, label)



# drawing special effects
def wait(wait_time):
    wait_time = wait_time * 0.01
    start_time = time.time()


    while time.time() - start_time < wait_time:
        blt.refresh()

def draw_effect(x,y, tile, speed, clear, color="white"):
    blt.layer(3)
    blt.color(color)
    blt.put_ext(x, y, 0, 0, tile)
    wait(8*speed)
    if clear:
        blt.clear_area(x,y)

def draw_effect_mult(x,y,tile, speed, color="white"):
    blt.layer(3)
    blt.color(color)
    blt.put_ext(x, y, 0, 0, tile)

def draw_effects_batch(effects, speed, clr_x, clr_y, clr_w=1, clr_h=1):
    for eff in effects:
        draw_effect_mult(eff[1], eff[2], eff[0], speed, eff[3])

    wait(8*speed)
    blt.clear_area(clr_x, clr_y, clr_w, clr_h)


def draw_effects(effects, speed, clr_x, clr_y, clr_w=1, clr_h=1):
    for eff in effects:
        draw_effect(eff[1],eff[2], eff[0], speed, False, eff[3])

    blt.clear_area(clr_x,clr_y, clr_w, clr_h)

def draw_floating_text(x,y, string):
    effects = []
    w = 1
    for l in str(string):
        effects.append((l, x, y, "white"))
        x +=1
        w +=1

    draw_effects_batch(effects, 5, x, y, w, 1)

def draw_floating_text_step(x,y, string):
    effects = []
    w = 1
    for l in str(string):
        effects.append((l,x,y, "white"))
        x += 1
        w += 1

    draw_effects(effects, 2, x, y, w, 1)

if __name__ == "__main__":
    # use it for testing
    pass