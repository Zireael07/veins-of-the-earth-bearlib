
import generators
import components
import events

# item use effects
def cast_heal(actor):
    if actor.creature.hp == actor.creature.max_hp:
        events.notify(events.GameEvent("MESSAGE", ("You are already fully healed!", "red")))
        #GAME.game_message("You are already fully healed!", "red")
        return 'cancelled'

    heal = generators.roll(1,8)
    events.notify(events.GameEvent("MESSAGE", ("You healed " + str(heal) + " damage", "violet")))
    #GAME.game_message("You healed " + str(heal) + " damage", "violet")
    actor.creature.heal(heal)

def cast_strength(actor):
    str_buff = components.Effect("Strength", "green", 4, 2)
    str_buff.apply_effect(actor.creature)
    events.notify(events.GameEvent("MESSAGE", ("You cast strength!", "pink")))

def eat_food(actor):
    if actor.creature.player and actor.creature.player.nutrition < 500:
        events.notify(events.GameEvent("MESSAGE", ("You ate your food", "light green")))
        actor.creature.player.nutrition += 150

    else:
        events.notify(events.GameEvent("MESSAGE", ("You are full, you cannot eat any more", "light yellow")))

def drink(actor):
    if actor.creature.player and actor.creature.player.thirst < 300:
        events.notify(events.GameEvent("MESSAGE", ("You drank from the flask", "light blue")))
        actor.creature.player.thirst += 150

    else:
        events.notify(events.GameEvent("MESSAGE", ("You are full, you cannot drink any more", "light yellow")))