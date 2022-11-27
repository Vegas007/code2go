from app import *


def print_error(*args):
    """
    :param args: string
    """
    if not DEBUG:
        return

    for arg in args:
        print(arg)


def get_file_ext(file_name):
    """
    :param file_name: string
    :return: string
    """
    return file_name.rsplit('.', 1)[1].lower()
