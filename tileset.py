# coding: utf8

from bearlibterminal import terminal as blt

# tiles
def set_tiles():
    blt.set("0x3002: gfx/floor_cave.png, align=center")  # "."
    blt.set("0x3003: gfx/floor_sand.png, align=center")
    blt.set("0x23: gfx/wall_stone.png, align=center")  # "#"
    blt.set("0x2503: gfx/wall_stone_vert_EW.png, align=center")  # "│" #2502 is used by window rendering
    blt.set("0x003E: gfx/stairs_down.png, align=center")  # ">"
    blt.set("0x003C: gfx/stairs_up.png, align=center")  # "<"
    blt.set("0x2317: gfx/bed.png, align=center")
    blt.set("0x266F: gfx/crate.png, align=center")
    # player
    blt.set("0x40: gfx/human_m.png, align=center")  # "@"
    # NPCs (we use Unicode private area here)
    blt.set("0xE000: gfx/kobold.png,  align=center")  # ""
    blt.set("0xE001: gfx/goblin.png, align=center")
    blt.set("0xE002: gfx/drow_fighter.png, align=center")
    blt.set("0xE003: gfx/human.png, align=center")
    blt.set("0xE004: gfx/child.png, align=center")
    # items
    blt.set("0x2215: gfx/longsword.png, align=center")  # "∕"
    blt.set("0x1C0: gfx/dagger.png, align=center")  # "ǀ"
    blt.set("0xFF3B: gfx/chain_armor.png, align=center")  # "［"
    blt.set("0xFF09: gfx/armor_leather.png, align=center")  # ")"
    blt.set("0xFF08: gfx/armor_studded.png, align=center")  # "("
    blt.set("0x2762: gfx/potion.png, align=center")  # "❢"
    blt.set("0x1F35E: gfx/food.png, align=center")  # bread unicode symbol
    blt.set("0x2615: gfx/flask.png, align=center")  # hot beverage symbol
    blt.set("0x2053: gfx/torch.png, align=center")
    blt.set("0x3C9: gfx/boots.png, align=center") # "ω"
    blt.set("0xA7B7: gfx/boots2.png, align=center")
    blt.set("0x3009: gfx/shield_light_wooden.png, align=center") #"〉"
    blt.set("0x2102: gfx/helmet_metal.png, align=center")

    # gfx
    blt.set("0x2317: gfx/mouseover.png, align=center")  # "⌗"
    blt.set("0x2017: gfx/unit_marker.png, align=center")  # "̳"
    blt.set("0x2BC1: gfx/splash_gray.png, align=center")  # "⯁"
    blt.set("0x2BC2: gfx/splash_shield.png, align=center")  # "⯂"

    # paperdoll
    blt.set("0xE200: gfx/paperdoll/chainmail.png, align=center")
    blt.set("0xE201: gfx/paperdoll/leather_armour.png, align=center")
    blt.set("0xE202: gfx/paperdoll/long_sword_right.png, align=center")
    blt.set("0xE203: gfx/paperdoll/leg_armor04.png, align=center")
    blt.set("0xE204: gfx/paperdoll/helm_plume.png, align=center")