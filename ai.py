import libtcodpy as libtcod
import math

import constants
from tile_lookups import get_block_path


# need a reference to global GAME %^$@
def initialize_game(game):
    #print("[AI] initialized game")
    global GAME
    GAME = game

# AI
class AI_test(object):
    def take_turn(self, player, fov_map):
        # print("AI taking turn")
        # check distance to player
        dx = player.x - self.owner.x
        dy = player.y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #print("Distance to player is " + str(distance))

        # if we can see it, it can see us too
        #if libtcod.map_is_in_fov(fov_map, self.owner.x, self.owner.y):

        #ai fov
        libtcod.map_compute_fov(fov_map, self.owner.x, self.owner.y, constants.LIGHT_RADIUS, constants.FOV_LIGHT_WALLS,
                                constants.FOV_ALGO)

        # if not in fov
        if not libtcod.map_is_in_fov(fov_map, player.x, player.y):

        #if distance > 5:
            #print("AI distance > 5, random move")
            self.owner.creature.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1), GAME.level.current_map)
        else:
            if self.owner.creature.faction != player.creature.faction:
                is_neutral_faction = GAME.get_faction_reaction(self.owner.creature.faction, player.creature.faction, False) == 0
                if is_neutral_faction:
                    self.owner.creature.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1),
                                             GAME.level.current_map)
                else:
                    #print("AI distance less than 5, moving towards player")
                    move_astar(self.owner, player, GAME.level.current_map)
                    #self.owner.creature.move_towards(player.x, player.y, GAME.level.current_map)

def death_monster(monster):
    if monster.visible:
        GAME.game_message(monster.creature.name_instance + " is dead!", "gray")

    # spawn loot
    #GAME.level.current_entities.append(generate_item("dagger", monster.x, monster.y))

    if monster.container is not None:
        print("Monster had inventory")
        for item in monster.container.inventory:
            print("Spawning an item from inventory")
            item.x = monster.x
            item.y = monster.y
            GAME.level.current_entities.append(item)
            item.send_to_back()

    # clean up components
    monster.creature = None
    monster.ai = None
    # remove from map
    GAME.level.current_entities.remove(monster)

def move_astar(actor, target, inc_map):
    #Create a FOV map that has the dimensions of the map
    fov = libtcod.map_new(constants.MAP_WIDTH, constants.MAP_HEIGHT)

    #Scan the current map each turn and set all the walls as unwalkable
    for y1 in range(constants.MAP_HEIGHT):
        for x1 in range(constants.MAP_WIDTH):
            libtcod.map_set_properties(fov, x1, y1,
                                       not get_block_path(inc_map[x1][y1]),
                                       not get_block_path(inc_map[x1][y1]))


    #Scan all the entities to see if there are objects that must be navigated around
    #Check also that the entity isn't self or the target (so that the start and the end points are free)
    #The AI class handles the situation if self is next to the target so it will not use this A* function anyway
    for ent in GAME.level.current_entities:
        if ent.creature and ent != actor and ent != target:
            #Set the tile as a wall so it must be navigated around
            libtcod.map_set_properties(fov, ent.x, ent.y, True, False)

    #Allocate a A* path
    #The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
    my_path = libtcod.path_new_using_map(fov, 1.41)

    #Compute the path between self's coordinates and the target's coordinates
    libtcod.path_compute(my_path, actor.x, actor.y, target.x, target.y)

    #Check if the path exists, and in this case, also the path is shorter than 25 tiles
    #The path size matters if you want the monster to use alternative longer paths (for example through other rooms) if for example the player is in a corridor
    #It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
    if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
        #Find the next coordinates in the computed full path
        x, y = libtcod.path_walk(my_path, True)
        if x or y:
            # Move to next path
            actor.creature.move_towards(x,y, inc_map)
    #else:
        #Keep the old move function as a backup so that if there are no paths (for example another monster blocks a corridor)
        #it will still try to move towards the player (closer to the corridor opening)
     #   self.move_towards(target.x, target.y)

    #Delete the path to free memory
    libtcod.path_delete(my_path)