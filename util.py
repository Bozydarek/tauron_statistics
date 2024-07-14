import sys
from enum import StrEnum

from typing import Any, Union, Sequence


Numeric = Union[int, float]


# output table properties
WIDTH = 8
PRECISION = 2


class Color(StrEnum):
    RED = '\033[91m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    END = '\033[0m'


# TODO: replace with "logging"
def print_note(*msg: Sequence[Any]) -> None:
    print(f"{Color.BLUE}[NOTE]{Color.END}", *msg, file=sys.stderr)


def print_wrn(*msg: Sequence[Any]) -> None:
    print(f"{Color.PURPLE}[WARNING]{Color.END}", *msg, file=sys.stderr)


def print_err(*msg: Sequence[Any], interrupt: bool = True) -> None:
    print(f"{Color.RED}[ERROR]{Color.END}", *msg, file=sys.stderr)
    if interrupt:
        exit(1)


def balance_color(num: Numeric, padding: int = 0, unit: str = "") -> str:
    if isinstance(num, float):
        out = f"{num:.{PRECISION}f}"

    if unit != "" and not unit.startswith(" "):
        unit = " " + unit

    return (
        f"{Color.RED if num < 0 else Color.GREEN}"
        f"{out:>{padding}}{unit}{Color.END}")
