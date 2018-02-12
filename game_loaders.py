import jsonpickle
import json

# save/load
def save_game(game, camera, player):
    data = {
        'serialized_player_index': jsonpickle.encode(game.level.current_entities.index(player)),
        'serialized_cam': jsonpickle.encode(camera),
        'serialized_game': jsonpickle.encode(game),
    }

    #test
    print data['serialized_player_index']

    # write to file
    with open('savegame.json', 'w') as save_file:
        json.dump(data, save_file, indent=4)

def load_game():
    with open('savegame.json', 'r') as save_file:
        data = json.load(save_file)

    game = jsonpickle.decode(data['serialized_game'])
    player_index = jsonpickle.decode(data['serialized_player_index'])
    camera = jsonpickle.decode(data['serialized_cam'])

    player = game.level.current_entities[player_index]

    return game, player, camera