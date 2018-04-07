from noisemap import NoiseMapGenerator
from map_common import print_map_string, Directions, Rect
from tile_lookups import TileTypes, get_index

# for histogram
from collections import namedtuple
Info = namedtuple('Info', 'start height')
# sorting
from operator import itemgetter

class MainMapGenerator(NoiseMapGenerator):
    def __init__(self, map_width, map_height, seed, lacunarity=2.0, hurst=0.5, noise_zoom=1, noise_octaves=10, debug=False):

        super(MainMapGenerator, self).__init__(map_width, map_height, seed, lacunarity, hurst, noise_zoom, noise_octaves, debug)


    # step one of finding rectangle of floor in matrix
    # https://stackoverflow.com/a/12387148
    def num_unbroken_floors_columns(self):
        num_floors = [[0 for _ in range(self.map_height)] for _ in range(self.map_width)]

        for x in range(0, self.map_width):
            for y in range(0, self.map_height):
                north = (x + Directions.NORTH[0], y + Directions.NORTH[1])
                num_floors[x][y] = 1 + num_floors[north[0]][north[1]] if self._map[x][y] == get_index(TileTypes.FLOOR) else 0

        return num_floors

    # parse it nicely
    def unbroken_floors_columns_get(self, num_floors):
        floors = []
        for y in range(len(num_floors)):
            row = []
            for x in range(len(num_floors[0])):
                row.append(num_floors[x][y])

            floors.append(row)

        return floors

    def unbroken_floors_columns_print(self, num_floors):
        list_str = []
        for y in range(len(num_floors)):
            for x in range(len(num_floors[0])):
                list_str.append(str(num_floors[x][y]))

            # our row ended, add a line break
            list_str.append("\n")

        string = ''.join(list_str)
        # print string
        return string

    # max area rect under histogram
    # based on https://stackoverflow.com/a/4690790
    def max_rectangle_area(self, histogram, hist_index):
        """Find the area of the largest rectangle that fits entirely under
        the histogram.
        Return: rect (x,y,w,h), area
        """

        #print("Histogram: " + str(histogram) + " " + str(len(histogram)))

        stack = []
        top = lambda: stack[-1]
        max_area = 0
        # new
        rects = []
        res = None

        pos = 0  # current position in the histogram
        for pos, height in enumerate(histogram):
            #print("Index " + str(histogram.index(pos, height)))
            start = pos  # position where rectangle starts
            while True:
                if not stack or height > top().height:
                    stack.append(Info(start, height))  # push
                elif stack and height < top().height:
                    # this line goofed up max area for some histograms
                    #max_area = max(max_area, top().height * (pos - top().start))
                    start, _ = stack.pop()
                    continue
                break  # height == top().height goes here

        pos += 1
        for start, height in stack:
            #print("Pos " + str(pos) + " i: " + str(stack.index(start, height)))
            width = (pos - start)
            area = height * width
            # print("From stack: start:" + str(start) + " h: " + str(height) + " w: " + str(width) + " area: " + str(area))

            max_area = max(max_area, area)

            rects.append((start, height, width, area))

        print("Max area in line: " + str(max_area))

        # added by yours truly, TODO: can we do this somewhere earlier?
        for r in rects:
            start, height, width, area = r
            # print("From stack: start:" + str(start) + " h: " + str(height) + " w: " + str(width) + " area: " + str(area))
            # are we the biggest? get additional info
            if area == max_area:
                # we want width and height and start position in addition to area
                # i = stack.index((start, height))
                # print("Biggest rectangle index: " + str(i) + " for y: " + str(hist_index))
                print("Biggest for y: " + str(hist_index) + " start: " + str(start) + " h: " + str(
                    height) + " w: " + str(width) + " area: " + str(area))


                # we assigned 1 for the first free cell in a column, but a Rect with a height of 1 is x+1 not x
                # so we need to deduce 1 (so we get x and not x+1)
                # this algo is bottom-up, rect is top-down - deduce height from y and add 1 so that we cover the bottom line
                res = Rect(start, hist_index-height+1, width, height-1), hist_index

        return max_area, res

    # step two of finding rectangle of floor in matrix
    # https://stackoverflow.com/a/12387148
    def largest_area_rects(self, floors):
        rects = []
        # reverse order
        for y in range(len(floors) - 1, -1, -1):
            #print("Index: " + str(y))
            #print(str(floors[y]))

            rect = self.max_rectangle_area(floors[y], y)

            # discard all rects whose area is 0 or 1 (TODO: why do they happen?)
            if rect[0] > 1:
                 #print("Appending: " + str(rect))
                 rects.append(rect)

        # this sorts in ascending order
        sort = sorted(rects, key=itemgetter(0))
        # .. so we need the last entry
        return sort[len(sort) - 1]

    def fill_big_rect(self, big_rect):
        for x in range(big_rect.x1, big_rect.x2+1):
            for y in range(big_rect.y1, big_rect.y2+1):
                # paranoia
                if x < self.map_width and y < self.map_height:
                    # debugging
                    self._map[x][y] = get_index(TileTypes.CRATE)


if __name__ == '__main__':

    #test map generation

    # default
    map_gen = MainMapGenerator(40, 40, 2)
    current_map = map_gen.generate_map(False)

    print_map_string(current_map)

    # bigger
    map_gen = MainMapGenerator(60,60,2)
    current_map = map_gen.generate_map(False)

    print_map_string(current_map)



    # test special stuff
    floors = map_gen.num_unbroken_floors_columns()
    # pretty
    #print(map_gen.unbroken_floors_columns_print(floors))

    # get tidy rows from the floors 2d array
    row_floors = map_gen.unbroken_floors_columns_get(floors)
    #print(row_floors)

    largest = map_gen.largest_area_rects(row_floors)

    big_rect = largest[1][0]
    index = largest[1][1]


    print("Largest: " + "index: " + str(index) + " x " + str(big_rect.x1) + ",y " + str(big_rect.y1) +
            " w: " + str(big_rect.x2-big_rect.x1) + " h: " + str(big_rect.y2-big_rect.y1))
          #" to x: " + str(big_rect.x2) + ",y: " + str(big_rect.y2))

    map_gen.fill_big_rect(big_rect)

    print_map_string(current_map)