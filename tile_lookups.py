# based on https://stackoverflow.com/questions/2682745/how-do-i-create-a-constant-in-python/20508128#20508128

class Tile_Lookups(object):
    """
    Create objects that can be accessed with Tile_Lookups.WALL

    """

    def __init__(self, *args, **kwargs):
        self.dict = dict(*args, **kwargs)

        # this assumes values are tuples
        self.test = dict((value) for key, value in self.dict.iteritems())

        #self.reverse = dict((value, key) for key, value in self.dict.iteritems())

    def __iter__(self):
        return iter(self.dict)

    def __len__(self):
        return len(self.dict)

    # NOTE: This is only called if self lacks the attribute.
    # So it does not interfere with get of 'self.dict', etc.
    def __getattr__(self, name):
        return self.dict[name]

    # ASSUMES '_..' attribute is OK to set. Need this to initialize 'self.dict', etc.
    #If use as keys, they won't be constant.
    def __setattr__(self, name, value):
        super(Tile_Lookups, self).__setattr__(name, value)

        # we don't need the locking behavior and this prevented iteritems() from working
        # if (name[0] == '_'):
        #     super(Constants, self).__setattr__(name, value)
        #     #print(value)
        # else:
        #     raise ValueError("setattr while locked", self)

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
                         BED=(5, struc_Tile("bed", 0x2317, "}", False)),
                         CRATE=(6, struc_Tile("crates", 0x266F, "&", False))
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