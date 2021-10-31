from typing import List, Tuple
from sbs.colors import *


def menu(options: List[str], default: int = None):
    for option, index in zip(options, range(len(options))):
        print(f"[{index}] {option}")
    done = False
    while not done:
        if default:
            i = input(f"[{options[default]}]> ")
            if not i:
                i = default
        else:
            i = input(f"> ")
        try:
            i = int(i)
        except ValueError:
            continue

        if 0<i<len(options):
            done = True
    return i
