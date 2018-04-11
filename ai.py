import libtcodpy as libtcod
import math

import constants
from tile_lookups import get_block_path
from map_common import random_free_tile_away, direction_to, Directions
import events
import game_vars

# need a reference to global GAME %^$@
#def initialize_game(game):
    #print("[AI] initialized game")
#    global GAME
#    GAME = game

# directions for AI to try in order
EastDirs = [Directions.EAST, Directions.SOUTHEAST, Directions.NORTHEAST,
            Directions.SOUTH, Directions.NORTH, Directions.NORTHWEST, Directions.SOUTHWEST, Directions.WEST ]
WestDirs = [Directions.WEST, Directions.NORTHWEST, Directions.SOUTHWEST,
            Directions.SOUTH, Directions.NORTH, Directions.NORTHEAST, Directions.SOUTHEAST, Directions.EAST ]
NorthDirs = [Directions.NORTH, Directions.NORTHWEST, Directions.NORTHEAST,
             Directions.EAST, Directions.WEST, Directions.SOUTHWEST, Directions.SOUTHEAST, Directions.SOUTH ]
SouthDirs = [Directions.SOUTH, Directions.SOUTHEAST, Directions.SOUTHWEST,
             Directions.WEST, Directions.EAST, Directions.NORTHWEST, Directions.NORTHEAST, Directions.NORTH ]
NEDirs = [Directions.NORTHEAST, Directions.NORTH, Directions.EAST,
          Directions.NORTHWEST, Directions.SOUTHEAST, Directions.SOUTH, Directions.WEST, Directions.SOUTHWEST ]
SEDirs = [Directions.SOUTHEAST, Directions.SOUTH, Directions.EAST,
          Directions.NORTHEAST, Directions.SOUTHWEST, Directions.NORTH, Directions.WEST, Directions.NORTHWEST ]
NWDirs = [Directions.NORTHWEST, Directions.NORTH, Directions.WEST,
          Directions.NORTHEAST, Directions.SOUTHWEST, Directions.SOUTH, Directions.EAST, Directions.SOUTHEAST ]
SWDirs = [Directions.SOUTHWEST, Directions.SOUTH, Directions.WEST,
          Directions.NORTHWEST, Directions.SOUTHEAST, Directions.NORTH, Directions.EAST, Directions.NORTHEAST ]

DIR_TO_LIST = {
    Directions.EAST: EastDirs,
    Directions.WEST: WestDirs,
    Directions.NORTH: NorthDirs,
    Directions.SOUTH: SouthDirs,
    Directions.NORTHEAST: NEDirs,
    Directions.SOUTHEAST: SEDirs,
    Directions.NORTHWEST: NWDirs,
    Directions.SOUTHWEST: SWDirs,
}

# AI
class AI(object):
    def __init__(self):
        self.target = None

    def distance(self, player):
        # check distance to player
        dx = player.x - self.owner.x
        dy = player.y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # print("Distance to player is " + str(distance))

        return distance

    @staticmethod
    def consider_move(tx, ty, game_map):
        if tx >= len(game_map) or tx < 0:
            print("Not in bounds")
            return False

        if ty >= len(game_map[0]) or ty < 0:
            print("Not in bounds")
            return False

        if get_block_path(game_map[tx][ty]) == True:
            print("Blocked")
            return False

        return True

    def consider_move_list(self, direction, game_map):
        list_try = DIR_TO_LIST[direction]

        ret = None

        for d in list_try:
            print(str(self.owner.name) + " considering ..." + str(d))
            tx = self.owner.x + d[0]
            ty = self.owner.y + d[1]

            if self.consider_move(tx, ty, game_map):
                ret = d
                print(str(self.owner.name) + " picked: " + str(ret))
                break

        return ret


class EnemyAI(AI):
    def take_turn(self, player, fov_map):
        #print("AI taking turn")

        # if we can see it, it can see us too
        #if libtcod.map_is_in_fov(fov_map, self.owner.x, self.owner.y):

        #ai fov
        libtcod.map_compute_fov(fov_map, self.owner.x, self.owner.y, self.owner.creature.get_light_radius(), constants.FOV_LIGHT_WALLS,
                                constants.FOV_ALGO)

        # if not in fov
        if not libtcod.map_is_in_fov(fov_map, player.x, player.y):
            random_int = libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1, 1)
            direct = direction_to(self.owner, (self.owner.x+random_int[0], self.owner.y+random_int[1]))
            if direct is not Directions.CENTER:
                cons = self.consider_move_list(direct, game_vars.level.current_map)
                self.owner.creature.move_direction(cons, game_vars.level.current_map)
        else:
            print("Player in fov")
            cons = self.consider_move_list(direction_to(self.owner, player), game_vars.level.current_map)
            self.owner.creature.move_direction(cons, game_vars.level.current_map)

            #move_astar(self.owner, player, game_vars.level.current_map)
            #self.owner.creature.move_towards(player.x, player.y, game.level.current_map)

class NeutralAI(AI):
    def take_turn(self, player, fov_map):
        # print("AI taking turn")

        # ai fov
        libtcod.map_compute_fov(fov_map, self.owner.x, self.owner.y, self.owner.creature.get_light_radius(), constants.FOV_LIGHT_WALLS,
                                constants.FOV_ALGO)

        # if not in fov
        if not libtcod.map_is_in_fov(fov_map, player.x, player.y):
            random_int = libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1)
            direct = direction_to(self.owner, (self.owner.x + random_int[0], self.owner.y + random_int[1]))
            if direct is not Directions.CENTER:
                cons = self.consider_move_list(direct, game_vars.level.current_map)
                self.owner.creature.move_direction(cons, game_vars.level.current_map)
        else:
            if not self.target:
                self.target = random_free_tile_away(game_vars.level.current_map, 6, (self.owner.x, self.owner.y))

            self.owner.creature.move_direction(direction_to(self.owner, self.target), game_vars.level.current_map)

           #move_astar(self.owner, self.target, game_vars.level.current_map)




def death_monster(monster):
    if monster.visible:
        events.notify(events.GameEvent("MESSAGE", (monster.creature.name_instance + " is dead!", "gray")))

    # spawn loot
    if monster.container is not None:
        print("Monster had inventory")
        for item in monster.container.inventory:
            print("Spawning an item from inventory")
            item.x = monster.x
            item.y = monster.y
            game_vars.level.current_entities.append(item)
            item.send_to_back()

    # clean up components
    monster.creature = None
    monster.ai = None
    # remove from map
    game_vars.level.current_entities.remove(monster)

def move_astar(actor, target, inc_map):
    #print("Astar target: " + str(target))


    #Create a FOV map that has the dimensions of the map
    fov = libtcod.map_new(len(inc_map), len(inc_map[0]))

    #Scan the current map each turn and set all the walls as unwalkable
    for y1 in range(len(inc_map[0])):
        for x1 in range(len(inc_map)):
            libtcod.map_set_properties(fov, x1, y1,
                                       not get_block_path(inc_map[x1][y1]),
                                       not get_block_path(inc_map[x1][y1]))


    #Scan all the entities to see if there are objects that must be navigated around
    #Check also that the entity isn't self or the target (so that the start and the end points are free)
    #The AI class handles the situation if self is next to the target so it will not use this A* function anyway
    for ent in game_vars.level.current_entities:
        if ent.creature and ent != actor and ent != target:
            #Set the tile as a wall so it must be navigated around
            libtcod.map_set_properties(fov, ent.x, ent.y, True, False)

    # convert to tuple if not already one (we can't do it earlier because of the target exclusion above)
    if hasattr(target, "x"):
        target = (target.x, target.y)

    #Allocate a A* path
    #The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
    my_path = libtcod.path_new_using_map(fov, 1.41)

    #Compute the path between self's coordinates and the target's coordinates
    libtcod.path_compute(my_path, actor.x, actor.y, target[0], target[1])

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