import csv
import sys
from enum import StrEnum
from datetime import date

import yaml

from typing import Any, Union, Sequence

from data_processor import DataPoint

Numeric = Union[int, float]


# output table properties
WIDTH = 8
PRECISION = 2


class Color(StrEnum):
    RED = '\033[91m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    END = '\033[0m'


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


def load_cache() -> list[DataPoint]:
    data = []
    try:
        with open('cache.csv') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in reader:
                if len(row) != 6:
                    raise ValueError(
                        f"each row supposed to have 6 elements, "
                        f"{len(row)} found instead.")

                data.append(DataPoint(
                    date.fromisoformat(row[0]),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                    int(row[4]),
                    int(row[5]),
                ))
    except IOError:
        print_wrn("Cache file is not accessible.")
    except ValueError as e:
        print_wrn(f"Cache file is corrupted: {e}")
        return []

    return data


def load_config() -> dict[str, Any]:
    with open("config.yml", 'r') as config_file:
        try:
            config = yaml.safe_load(config_file)
        except yaml.YAMLError as e:
            print_err(f"There is a problem with configuration file: {e}")
        else:
            print("Configuration file loaded.")
    return config


def save_cache(
        data: list[DataPoint], date_today: date) -> None:

    data_to_save = data
    if (data_to_save[-1].month.year == date_today.year and
            data_to_save[-1].month.month == date_today.month):
        data_to_save = data[:-1]

    print("Save cache...")
    with open('cache.csv', 'w') as csvfile:
        cache = csv.writer(
            csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        cache.writerows(data_to_save)
