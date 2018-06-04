# coding: utf8
from bearlibterminal import terminal as blt

import renderer
from map_common import distance_to, tiles_distance_to, get_map_desc, map_check_for_creature, Directions
import game_vars
import constants
import handle_input

# need the refs
def initialize_player(player):
    global PLAYER
    PLAYER = player


# debugging rooms
def get_room_index():
    room_index = -1
    for r in game_vars.level.rooms:

        if r.contains((PLAYER.x, PLAYER.y)):
            room_index = game_vars.level.rooms.index(r)
            break

    return room_index

def room_index_str():
    index = get_room_index()

    if index != -1:
        return str(index)
    else:
        return "None"

def get_room_from_index(index):
    if index != -1:
        return game_vars.level.rooms[index]

def get_room_data():
    index = get_room_index()
    if index != -1:
        room = get_room_from_index(index)
        return "Center: " + str(room.center()) + " x " + str(room.x1) + " y " + str(room.y1) +\
               " x2 " + str(room.x2) + " y2 " + str(room.y2) +\
               " width " + str(room.x2-room.x1) + " height " + str(room.y2-room.y1)
    else:
        return "None"

# descriptions
def show_npc_desc(pix_x, pix_y):
    w = 4
    h = 10
    iso_x, iso_y = renderer.pix_to_iso(pix_x, pix_y)
    taken = map_check_for_creature(iso_x, iso_y)
    if taken is not None and taken.creature.player is None:
        hp_perc = (taken.creature.hp*100.0/taken.creature.max_hp) # *100.0
        blt.layer(1)
        # draw the npc
        blt.puts(w, h, u"%c  %s" % (taken.char, taken.creature.name_instance) )
        blt.puts(w,h+2, "Enemy hp: " + str(taken.creature.hp) + " " + str(hp_perc) + "%")
        # chance to hit
        melee = PLAYER.creature.melee*1.0/100.0
        not_dodged = (100-taken.creature.dodge)*1.0/100.0
        blt.puts(w, h+3, "Chance to hit: %.2f + %.2f = %.2f " % (melee, not_dodged, melee*not_dodged) )
        blt.layer(0)

def show_tile_desc(pix_x, pix_y, fov_map):
    if not hasattr(game_vars.level, 'map_desc'):
        return
    w = 4
    h = 8
    iso_x, iso_y = renderer.pix_to_iso(pix_x, pix_y)

    dist = round(distance_to((iso_x, iso_y), (PLAYER.x, PLAYER.y)), 2)
    tiles_dist = tiles_distance_to((iso_x, iso_y), (PLAYER.x, PLAYER.y))

    blt.layer(1)
    blt.puts(w,h+1, "Dist: real:" + str(dist) + " tiles: " + str(tiles_dist) + " ft: " + str(tiles_dist*5) + " ft.")
    blt.puts(w, h, get_map_desc(iso_x, iso_y, fov_map, game_vars.level.current_explored, game_vars.level.map_desc))
    blt.layer(0)


DIR_TO_ARROW = {
    Directions.EAST: '↘',
    Directions.WEST: '↖',
    Directions.NORTH: '↗',
    Directions.SOUTH: '↙',
    Directions.NORTHEAST: '→',
    Directions.SOUTHEAST: '↓',
    Directions.NORTHWEST: '↑',
    Directions.SOUTHWEST: '←',
    # bug fix
    Directions.CENTER: '.'
}



def draw_hud(pix_x, pix_y):
    # hud bars
    blt.layer(1)
    # draw body parts' hp
    x = 2
    for p in PLAYER.creature.body_parts:
        renderer.draw_bar(x,15,p.max_hp, str(p.name), p.hp, p.max_hp, "red", "darker red")
        x += p.max_hp+1

    #renderer.draw_bar(2, 15, 20, "HP", PLAYER.creature.hp, PLAYER.creature.max_hp, "red", "darker red",
    #                  str(PLAYER.creature.hp))
    renderer.draw_bar(2, 17, 20, "Nutrition", PLAYER.creature.player.nutrition, 500, "green", "darker green")
    renderer.draw_bar(2, 19, 20, "Thirst", PLAYER.creature.player.thirst, 300, "blue", "darker blue")

    blt.color(4294967295)

    # compass
    blt.puts(2, 21, "[color=yellow] ↑ NW (%s key) " % (handle_input.get_up_key()))

    # debug
    # on top of map
    blt.layer(1)
    blt.puts(2, 2, "[color=red] player position: %d %d" % (PLAYER.x, PLAYER.y))
    blt.puts(2, 5, "[color=red] camera offset: %d %d" % (game_vars.camera.offset[0], game_vars.camera.offset[1]))
    blt.puts(2, 6, "[color=red] vi keys: %s " % (str(constants.VI_KEYS)))


    # queue
    x = 25
    y = 1
    for i in range (len(PLAYER.creature.move_queue)-1):
        m = PLAYER.creature.move_queue[i]
        blt.puts(x, y, DIR_TO_ARROW[m])  #str(m))

        x += 2

        # add max length of (x,y) string
        #x += 8

    # overlay queue on map
    blt.layer(3)
    render_pos = constants.RENDER_POSITIONS
    from renderer import draw_iso
    for i in range(len(PLAYER.creature.path_moves)-1):
        p, m = PLAYER.creature.path_moves[i]
        x,y = p
        x,y = draw_iso(x, y, render_pos)
        blt.puts(x,y, DIR_TO_ARROW[m])

    blt.layer(1)
    # this works on map tiles
    show_tile_desc(pix_x, pix_y, game_vars.fov_map)
    show_npc_desc(pix_x, pix_y)