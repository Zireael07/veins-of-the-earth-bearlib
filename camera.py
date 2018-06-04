import constants
import game_vars

def iso_pos(x,y):
    # isometric
    offset_x = constants.CAMERA_OFFSET
    #hw = constants.HALF_TILE_WIDTH
    #hh = constants.HALF_TILE_HEIGHT
    tile_x = (x - y) * constants.HALF_TILE_WIDTH + offset_x
    tile_y = (x + y) * constants.HALF_TILE_HEIGHT
    return tile_x, tile_y

class obj_Camera(object):
    def __init__(self):
        self.width = 20  # 80 # blt.state(blt.TK_CELL_WIDTH)*80
        self.height = 20  # 25 # blt.state(blt.TK_CELL_HEIGHT)*25
        self.x, self.y = (0, 0)
        self.top_x, self.top_y = (0, 0)
        self.offset = (0, 0)
        # self.rectangle = Rect(self.top_x, self.top_y, self.width, self.height)

    def start_update(self, player):
        target_pos = (80, 20)
        cur_pos_x, cur_pos_y = iso_pos(player.x, player.y)
        self.offset = (target_pos[0] - cur_pos_x, target_pos[1] - cur_pos_y)

    def update(self):
        # this calculates cells
        self.x, self.y = game_vars.player.x, game_vars.player.y  # renderer.draw_iso(PLAYER.x, PLAYER.y)
        self.top_x, self.top_y = self.x - self.width / 2, self.y - self.height / 2
        # update rect
        # self.rectangle.update(self.top_x, self.top_y, self.width, self.height)

    def move(self, dx, dy):
        # print("Moving the camera by " + str(dx) + ", " + str(dy))
        # if we increase map x by 1, draw coordinates increase by 1/2 tile width, 1/2 tile height
        # reverse that since we want the camera to stay in same place
        x_change = (-constants.TILE_WIDTH / 2, -constants.TILE_HEIGHT / 2)
        # if we increase map y by 1, draw coordinates change by -1/2 tile_width, 1/2 tile height
        # reverse that since we want the camera to stay in one place
        y_change = (constants.TILE_WIDTH / 2, -constants.TILE_HEIGHT / 2)
        # print("Offset change for 1 x is " + str(x_change) + " for 1 y is " + str(y_change))
        # print("offset change for -1x is" + str((x_change[0]*-1, x_change[1]*-1)) + " for -1 y is" + str((y_change[0]*-1, y_change[1]*-1)))

        # print("Offset calculations x: " + str(self.offset[0]) + " " + str(x_change[0]*dx) + " " + str(y_change[0]*dy))
        # print("Offset calculations y: " + str(self.offset[1]) + " " + str(x_change[1]*dx) + " " + str(y_change[1]*dy))
        new_x = self.offset[0] + x_change[0] * dx + y_change[0] * dy
        new_y = self.offset[1] + x_change[1] * dx + y_change[1] * dy

        self.offset = (new_x, new_y)

    # camera extents to speed up rendering
    def get_width_start(self):
        if self.top_x > 0:
            return self.top_x
        else:
            return 0

    def get_width_end(self, map_draw):
        if self.top_x + self.width <= len(map_draw):  # constants.MAP_WIDTH:
            return self.top_x + self.width
        else:
            return len(map_draw)  # constants.MAP_WIDTH

    def get_height_start(self):
        if self.top_y > 0:
            return self.top_y
        else:
            return 0

    def get_height_end(self, map_draw):
        if self.top_y + self.height <= len(map_draw[0]):  # constants.MAP_HEIGHT:
            return self.top_y + self.height
        else:
            return len(map_draw[0])  # constants.MAP_HEIGHT