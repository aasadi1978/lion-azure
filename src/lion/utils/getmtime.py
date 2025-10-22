from os import path as os_path
from time import localtime, strftime


def getmtime(path):
    t = os_path.getmtime(path)
    return strftime('%Y-%m-%d %H:%M:%S', localtime(t))