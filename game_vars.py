
"""
Game variables
Practically a singleton but implemented in a more Pythonic way - as a module

"""
game_state = None
init_seed = None
level = [[]]
message_history = []

fov_map = None
ai_fov_map = None

factions = []
calendar_game = None

fov_recompute = True

camera = None
player = None