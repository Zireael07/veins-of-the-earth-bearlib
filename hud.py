from bearlibterminal import terminal as blt

import renderer
from map_common import distance_to, tiles_distance_to, get_map_desc, map_check_for_creature
import game_vars

# need the refs
#def initialize_game(game):
#    global GAME
#    GAME = game

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