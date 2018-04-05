import constants
from map_common import print_map_string

def map_create(pillars):
    #new_map = [[struc_Tile(False) for y in range(0, constants.MAP_HEIGHT)] for x in range(0, constants.MAP_WIDTH)]
    new_map = [[ 1 for _ in range(0, constants.MAP_HEIGHT)] for _ in range(0, constants.MAP_WIDTH)]

    for coords in pillars:
        new_map[coords[0]][coords[1]] = 0 #.block_path = True
        #new_map[12][12] = 0 #.block_path = True

    # walls around the map
    for x in range(constants.MAP_WIDTH):
        new_map[x][0] = 0 #.block_path = True
        new_map[x][constants.MAP_WIDTH-1] = 0 #.block_path = True

    for y in range(constants.MAP_HEIGHT):
        new_map[0][y] = 0 #.block_path = True
        new_map[constants.MAP_HEIGHT-1][y] = 0 #.block_path = True

    return new_map

if __name__ == '__main__':

    #test map generation
    test_attempts = 3
    for i in range(test_attempts):
        current_map = map_create([(10,10), (15,15)])

        print_map_string(current_map)