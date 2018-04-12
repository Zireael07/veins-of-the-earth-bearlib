from enum_constants import Tile_Lookups

class struc_Tile(object):
    def __init__(self, name, tile_put, map_str, block_path):
        self.block_path = block_path
        self.name = name
        self.map_str = map_str
        self.tile_put = tile_put


# outside of both classes
def tile_from_index(i):
    return TileTypes.test[i]

def get_index(val):
    return val[0]


def get_map_str_type(val):
    return val[1].map_str

def get_map_str(i):
    return tile_from_index(i).map_str

def get_char_type(val):
    return val[1].tile_put

def get_char(i):
    return TileTypes.test[i].tile_put

def get_block_path(i):
    return TileTypes.test[i].block_path



TileTypes = Tile_Lookups(WALL=(1,struc_Tile("wall", "#", "#", True)),
                         WALL_V=(2, struc_Tile("wall", 0x2503, "#", True)),
                         FLOOR=(3, struc_Tile("floor", 0x3002, ".", False)),
                         STAIRS=(4,struc_Tile("stairs", ">", ">", False)),
                         STAIRS_UP=(5,struc_Tile("stairs", "<", "<", False)),
                         BED=(6, struc_Tile("bed", 0x2317, "}", False)),
                         CRATE=(7, struc_Tile("crates", 0x266F, "&", False))
                      )



if __name__ == "__main__":


    # way to look up by string
    print(TileTypes.dict["FLOOR"])

    # doesn't work
    #print(TileTypes["FLOOR"])

    print("Wall is " + str(TileTypes.WALL))

    print("Wall index is " + str(get_index(TileTypes.WALL)))

    print("Map str is " + str(get_map_str_type(TileTypes.WALL)))

    print("Map char is " + str(hex(get_char_type(TileTypes.WALL_V))))

    print("Tile from index: " + str(tile_from_index(1)) + ", " + str(tile_from_index(1).name))

    print("Map str from index is: " + str(get_map_str(1)))

    print("Map char from index is: " + str(get_char(2)))