import game_vars
import constants
import level
import calendar
import events
import square_fov

from map_common import map_make_fov, find_stairs_to

from game_states import GameStates

class obj_Game(object):
    """Object that is basically here to communicate with the game variables"""
    def __init__(self, basic, init_seed=10):
        if not basic:
            game_vars.init_seed = self.initialize_seed(init_seed)
            data = level.load_level_data(constants.STARTING_MAP)
            if data is not None:
                game_vars.level = level.obj_Level(data[0], init_seed, False)
                game_vars.level.generate_items_monsters(data[1], data[2])
            else:
                game_vars.level = level.obj_Level(constants.STARTING_MAP, init_seed, False)
                game_vars.level.generate_items_monsters(6)

            game_vars.fov_map = map_make_fov(game_vars.level.current_map, False)

            game_vars.ai_fov_map = map_make_fov(game_vars.level.current_map, True)

            game_vars.calendar_game = calendar.obj_Calendar(1371)


            # use events for messages
            events.subscribers.append(self.events_handler)

        game_vars.fov_recompute = False


    @staticmethod
    def initialize_seed(seed=10):
        init_seed = seed
        print("Init seed: " + str(init_seed))
        return init_seed

    def events_handler(self, event):
        if event.type == "MESSAGE":
            self.game_message(event.data)
        elif event.type == "END_TURN":
            self.end_player_turn()

    @staticmethod
    def game_message(event_data):  # msg, msg_color, details=None):
        if len(event_data) > 2:
            game_vars.message_history.append((event_data[0], event_data[1], event_data[2]))
        else:
            game_vars.message_history.append((event_data[0], event_data[1], None))

    @staticmethod
    def add_faction(faction_data):
        game_vars.factions.append(faction_data)
        print "Added faction " + str(faction_data)
        # add the reverse mapping, too
        game_vars.factions.append((faction_data[1], faction_data[0], faction_data[2]))
        print "Added reverse faction " + str((faction_data[1], faction_data[0], faction_data[2]))

    @staticmethod
    def get_faction_reaction(faction, target_faction, log):
        if faction == target_faction:
            return 100

        for fact in game_vars.factions:
            if fact[0] == faction and fact[1] == target_faction:
                if log:
                    print("Faction reaction of " + fact[0] + " to " + fact[1] + " is " + str(fact[2]))
                return fact[2]

    @staticmethod
    def end_player_turn():
        # toggle game state to enemy turn
        game_vars.game_state = GameStates.ENEMY_TURN

    @staticmethod
    def set_player_turn():
        # set state to player turn
        game_vars.game_state = GameStates.PLAYER_TURN
        print("Set player turn")

    @staticmethod
    def map_calculate_fov():
        if game_vars.fov_recompute:
            game_vars.fov_recompute = False
            radius = game_vars.player.creature.get_light_radius()

            square_fov.recompute_fov(game_vars.fov_map, game_vars.player.x, game_vars.player.y, radius)


            # if radius > 1:
            #     libtcod.map_compute_fov(game_vars.fov_map, game_vars.player.x, game_vars.player.y, radius, constants.FOV_LIGHT_WALLS,
            #                             constants.FOV_ALGO)
            # # radius 1, we want to see in all directions, use a square fov instead of whatever is defined in constants
            # else:
            #     libtcod.map_compute_fov(game_vars.fov_map, game_vars.player.x, game_vars.player.y, 1,
            #                             constants.FOV_LIGHT_WALLS, libtcod.FOV_PERMISSIVE_6)
    @staticmethod
    def new_level_set():
        # add player
        game_vars.level.current_entities.append(game_vars.player)

        # place player in sensible place
        game_vars.player.creature.move_to_target(game_vars.level.player_start_x, game_vars.level.player_start_y, game_vars.level.current_map)

        # add stuff
        game_vars.level.generate_items_monsters()

        # global FOV_MAP
        game_vars.fov_map = map_make_fov(game_vars.level.current_map, False)
        # global AI_FOV_MAP
        game_vars.ai_fov_map = map_make_fov(game_vars.level.current_map, True)

        # force fov recompute
        game_vars.fov_recompute = True
        game_vars.redraw = True

        game_vars.camera.start_update(game_vars.player)

    def next_level(self, destination=None):
        events.notify(events.GameEvent("MESSAGE", ("You descend deeper in the dungeon", "violet")))

        if not destination:
            destination = "dungeon"

        print("Destination: " + str(destination))
        # make next level
        game_vars.level = level.obj_Level(destination)

        self.new_level_set()

    def previous_level(self, from_level):
        print("From level: " + str(from_level))
        events.notify(events.GameEvent("MESSAGE", ("You ascend back", "violet")))

        # re-make starting level from seed
        data = level.load_level_data(constants.STARTING_MAP)
        if data is not None:
            game_vars.level = level.obj_Level(data[0], game_vars.init_seed, False)
            game_vars.level.generate_items_monsters(data[1], data[2])
        else:
            game_vars.level = level.obj_Level(constants.STARTING_MAP, game_vars.init_seed, False)
            game_vars.level.generate_items_monsters(6)

        self.new_level_set()

        # move to down stairs
        #stairs = get_tiles_of_type(game_vars.level.current_map, "STAIRS")
        stairs = find_stairs_to(from_level)
        print(str(stairs))
        if len(stairs) > 0:
            print("Stairs found, moving to stairs")
            stairs_x, stairs_y = stairs[0]
        else:
            # crash prevention
            stairs_x, stairs_y = (0,0)

        print("Move to " + str(stairs_x) + " " + str(stairs_y))
        game_vars.player.creature.move_to_target(stairs_x, stairs_y, game_vars.level.current_map)

        # force fov recompute
        game_vars.fov_recompute = True
        game_vars.redraw = True

        game_vars.camera.start_update(game_vars.player)