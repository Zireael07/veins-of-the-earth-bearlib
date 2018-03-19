
import generators
import components

# need a reference to global GAME %^$@
def initialize_game(game):
    print("[Level] initialized game")
    global GAME
    GAME = game

# item use effects
def cast_heal(actor):
    if actor.creature.hp == actor.creature.max_hp:
        GAME.game_message("You are already fully healed!", "red")
        return 'cancelled'

    heal = generators.roll(1,8)
    GAME.game_message("You healed " + str(heal) + " damage", "violet")
    actor.creature.heal(heal)

def cast_strength(actor):
    str_buff = components.Effect("Strength", "green", 4, 2)
    str_buff.apply_effect(actor.creature)
    GAME.game_message("You cast strength!", "pink")

def eat_food(actor):
    if actor.creature.player and actor.creature.player.nutrition < 500:
        GAME.game_message("You ate your food", "light green")
        actor.creature.player.nutrition += 150

    else:
        GAME.game_message("You are full, you cannot eat any more", "light yellow")

def drink(actor):
    if actor.creature.player and actor.creature.player.thirst < 300:
        GAME.game_message("You drank from the flask", "light blue")
        actor.creature.player.thirst += 150

    else:
        GAME.game_message("You are full, you cannot drink any more", "light yellow")