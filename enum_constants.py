# Python 2.7 doesn't have an Enum, so we make our own
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse

    return type('Enum', (), enums)


# from https://stackoverflow.com/questions/2682745/how-do-i-create-a-constant-in-python/20508128#20508128
class Constants(object):
    """
    Create objects that can be accessed with Constants.WHATEVER
    """

    def __init__(self, *args, **kwargs):
        self.dict = dict(*args, **kwargs)

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
        super(Constants, self).__setattr__(name, value)

        # we don't need the locking behavior (in original) and it prevented iteritems() from working

# expand the Constants to allow two-way lookups
class Tile_Lookups(Constants):
    """
    Create objects that can be accessed with Tile_Lookups.WALL

    """
    def __init__(self, *args, **kwargs):
        super(Tile_Lookups, self).__init__(*args, **kwargs)

        # this assumes values are tuples
        self.test = dict((value) for key, value in self.dict.iteritems())

        #self.reverse = dict((value, key) for key, value in self.dict.iteritems())