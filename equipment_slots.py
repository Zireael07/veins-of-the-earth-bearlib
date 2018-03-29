# Python 2.7 doesn't have an Enum, so we make our own
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse

    return type('Enum', (), enums)


EquipmentSlots = enum(MAIN_HAND=1,
                  BODY=2,
                  LITE=3    )