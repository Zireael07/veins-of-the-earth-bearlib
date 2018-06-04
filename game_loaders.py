import jsonpickle
import json

import game_vars

# save/load
def save_game(game_obj, camera, player):
    data = {
        'serialized_player_index': jsonpickle.encode(game_vars.level.current_entities.index(player)),
        'serialized_cam': jsonpickle.encode(camera),
        'serialized_game_obj': jsonpickle.encode(game_obj),
        # new method of serializing game
        'serialized_state': jsonpickle.encode(game_vars.game_state),
        'serialized_seed': jsonpickle.encode(game_vars.init_seed),
        'serialized_level': jsonpickle.encode(game_vars.level),
        'serialized_message_history': jsonpickle.encode(game_vars.message_history),
        'serialized_factions': jsonpickle.encode(game_vars.factions),
        'serialized_calendar': jsonpickle.encode(game_vars.calendar_game),
    }

    #test
    print data['serialized_player_index']

    # write to file
    with open('savegame.json', 'w') as save_file:
        json.dump(data, save_file, indent=4)

def load_game():
    with open('savegame.json', 'r') as save_file:
        data = json.load(save_file)

    game_obj = jsonpickle.decode(data['serialized_game_obj'])

    # new method of deserializing game
    game_vars.game_state = jsonpickle.decode(data['serialized_state'])
    game_vars.init_seed = jsonpickle.decode(data['serialized_seed'])
    game_vars.level = jsonpickle.decode(data['serialized_level'])
    game_vars.message_history = jsonpickle.decode(data['serialized_message_history'])
    game_vars.factions = jsonpickle.decode(data['serialized_factions'])
    game_vars.calendar_game = jsonpickle.decode(data['serialized_calendar'])


    player_index = jsonpickle.decode(data['serialized_player_index'])
    camera = jsonpickle.decode(data['serialized_cam'])

    player = game_vars.level.current_entities[player_index]

    game_vars.player = player
    game_vars.camera = camera
    game_vars.game_obj = game_obj

    return game_obj, player, camera