from app import *


def print_error(*args):
    if not DEBUG:
        return

    for arg in args:
        print(arg)
