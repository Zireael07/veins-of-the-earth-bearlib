from bearlibterminal import terminal as blt


def game_main_loop():

    game_quit = False

    while not game_quit:
        key = blt.read()
        if key in (blt.TK_ESCAPE, blt.TK_CLOSE):
            game_quit = True


    blt.close()


def game_initialize():
    blt.open()

    blt.printf(1, 1, 'Hello, world!')
    blt.refresh()

if __name__ == '__main__':
    game_initialize()
    game_main_loop()


