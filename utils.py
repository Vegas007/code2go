import app


def print_error(*args):
    if not app.DEBUG:
        return

    for arg in args:
        print(arg)
