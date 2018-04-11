# encoding: UTF-8

from tile_lookups import get_block_path

class FOVMap(object):
# Originally from http://www.roguebasin.com/index.php?title=Python_shadowcasting_implementation
# by Björn Bergström

    # Multipliers for transforming coordinates to other octants:
    mult = [
                [1,  0,  0, -1, -1,  0,  0,  1],
                [0,  1, -1,  0,  0, -1,  1,  0],
                [0,  1,  1,  0,  0, -1, -1,  0],
                [1,  0,  0,  1, -1,  0,  0, -1]
            ]
    def __init__(self, tile_omap):
        self.tile_omap = tile_omap
        self.width, self.height = len(tile_omap), len(tile_omap[0])
        self.light = []
        for _ in range(self.width):
            self.light.append([0] * self.height)
        self.flag = 0

    def blocked(self, x, y):
        return (x < 0 or y < 0
                or x >= self.width or y >= self.height
                #or self.tile_omap[x][y].blocks_sight)
                or get_block_path(self.tile_omap[x][y]))

    def lit(self, x, y):
        # prevent crash
        if x >= self.width or y >= self.height:
            return False

        try:
            return self.light[x][y] == self.flag
        except ValueError:
            # even more crash prevention
            return False
            #raise ValueError, "Error for " + str(x) + " "  + str(y)

    def set_lit(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.light[x][y] = self.flag

    def _cast_light(self, cx, cy, row, start, end, radius, xx, xy, yx, yy):
        "Recursive lightcasting function"
        if start < end:
            return

        # restore from Bergstroem
        radius_squared = radius * radius

        for j in range(row, radius+1):
            dx, dy = -j-1, -j
            blocked = False
            while dx <= 0:
                dx += 1
                # Translate the dx, dy coordinates into map coordinates:
                X, Y = cx + dx * xx + dy * xy, cy + dx * yx + dy * yy
                # l_slope and r_slope store the slopes of the left and right
                # extremities of the square we're considering:
                l_slope, r_slope = (dx-0.5)/(dy+0.5), (dx+0.5)/(dy-0.5)
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                else:
                    # Our light beam is touching this square; light it:
                    if dx * dx + dy * dy < radius_squared:
                    #if abs(dx) + abs(dy) < radius:
                        self.set_lit(X, Y)
                    if blocked:
                        # we're scanning a row of blocked squares:
                        if self.blocked(X, Y):
                            new_start = r_slope
                            continue
                        else:
                            blocked = False
                            start = new_start
                    else:
                        if self.blocked(X, Y) and j < radius:
                            # This is a blocking square, start a child scan:
                            blocked = True
                            self._cast_light(cx, cy, j+1, start, l_slope,
                                             radius, xx, xy, yx, yy)
                            new_start = r_slope
            # Row is scanned; do next row unless last square was blocked:
            if blocked:
                break

    def do_fov(self, x, y, radius):
        "Calculate lit squares from the given location and radius"
        radius += 1
          # Thus, a radius value of N means you can see N
          # units away orthogonally (rather than N - 1 units).
        self.flag += 1
        self.set_lit(x, y)
        for octant in range(8):
            self._cast_light(x, y, 1, 1.0, 0.0, radius,
                             self.mult[0][octant], self.mult[1][octant],
                             self.mult[2][octant], self.mult[3][octant])

fovmap = None
def init_fov_map(tile_omap):
    global fovmap
    fovmap = FOVMap(tile_omap)
    return fovmap

def recompute_fov(fovmap, x,y, rad):
    fovmap.do_fov(x,y, rad)
