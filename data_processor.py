import csv
import yaml

from enum import Enum
from datetime import date
from dataclasses import dataclass

from typing import Any

from month import last_day_of_month
from util import print_err, print_wrn, print_note

RE_RETRIEVE_RATIO = 0.8  # 80% of cumulated energy sent to the grid


# From python3.11 'StrEnum' can be used
class DataTypes(str, Enum):
    """Energy types"""
    consume = 'consum'  # That is a value provided by Tauron
    oze = 'oze'

    def __str__(self) -> str:
        return self.value


DataTypes.consume.__doc__ = "Energy consumed (taken from the grid)"
DataTypes.oze.__doc__ = "Energy generated (sent back to the grid)"


def rfilter_nones(_list: list[Any | None]) -> list[Any]:
    """Remove None values from the list, starting from the end
    util the first non-None value."""

    # Find the index of the first non-None value from right
    idx = next((
        i for i, val in enumerate(reversed(_list)) if val is not None),
        None)

    if idx == 0:
        return _list

    return _list[:-idx] if idx is not None else []


@dataclass
class MonthlyData:
    """This dataclass represents data points from Tauron API.

    Args:
        month (date): Month for this data
        values (list[float]): List of all available data points (days)
        eng_sum (float): Accumulated energy (in this month)
        tariff (str): Tariff name (from contract)
        data_type (DataTypes): 'oze' or 'consume'
    """
    month: date
    values: list[float]
    eng_sum: float
    tariff: str
    data_type: DataTypes

    @classmethod
    def parseData(cls, data_type: DataTypes,
                  date: date, data: dict[str, Any]) -> 'MonthlyData':
        "Initialize DataPoint from a MonthlyData"
        if not all(key in data for key in ("values", "sum", "tariff")):
            raise ValueError("Provided data are in unsupported shape")

        # Filter out Nones
        values: list[float] = rfilter_nones(data["values"])

        return cls(
            month=date,
            values=values,
            eng_sum=data["sum"],
            tariff=data["tariff"],
            data_type=data_type
        )


@dataclass
class DataPoint:
    """This dataclass represents data points that are shown
    in the summary table, as well as saved in cache.

    Args:
        month (date): Month that is represented by this data point
        usage (float): Accumulated used (taken from grid) energy (monthly)
        oze (float): Accumulated energy given back to grid (in this month)
        balance (float): Energy balance (20% "fee" is taken into account)
        days (int): How many days was taken into account
        positive_days (int): # days in which we used less energy
                            then we send back to the grid
    """
    month: date
    usage: float  # kWh
    oze: float  # kWh
    balance: float  # kWh
    days: int  # TODO: consider renaming to last_day
    positive_days: int

    def __iter__(self):
        """To be used by CSV writer"""
        return iter([
            self.month.isoformat(),
            self.usage,
            self.oze,
            self.balance,
            self.days,
            self.positive_days,
        ])

    @classmethod
    def fromMonthlyData(cls, consume_data: MonthlyData, oze_data: MonthlyData,
                        start_date: date | None = None) -> 'DataPoint':
        """Initialize DataPoint from a MonthlyData

        Args:
            data (MonthlyData): MonthlyData object to parse
            start_date (date): If defined, ignores data points before that date
        """
        if (consume_data.data_type != DataTypes.consume or
                oze_data.data_type != DataTypes.oze):
            raise ValueError("Provided data in a wrong type.")

        if consume_data.month != oze_data.month:
            raise ValueError("Provided data are for different month.")

        processed_month = consume_data.month
        last_day = len(consume_data.values)

        # NOTE: Sometimes we want to exclude some data, for example when
        # installation date was in the middle of the month
        if (start_date is not None and
                start_date.year == processed_month.year and
                start_date.month == processed_month.month):
            # NOTE: This step might not be needed - after switching  to OZE
            # API return None values for day before OZE
            if last_day_of_month(start_date).day == len(consume_data.values):
                print_note("Trimming data...")
                day = start_date.day - 1  # Tables indexes start from 0
                consume_data.values = consume_data.values[day:]
                oze_data.values = oze_data.values[day:]
                # NOTE: We don't need to modify last day

        # NOTE: if start data is None, we could use precalculated sum (eng_sum)
        usage = sum(consume_data.values)
        oze_sum = sum(oze_data.values)
        balance = oze_sum * RE_RETRIEVE_RATIO - usage

        positive_days = sum(
            (o * RE_RETRIEVE_RATIO - c) > 0
            for c, o in zip(consume_data.values, oze_data.values))

        return cls(
            processed_month,
            usage,
            oze_sum,
            balance,
            last_day,
            positive_days)


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
            print_note("Configuration file loaded.")
    return config


def save_cache(
        data: list[DataPoint], date_today: date) -> None:

    data_to_save = data
    if (data_to_save[-1].month.year == date_today.year and
            data_to_save[-1].month.month == date_today.month):
        data_to_save = data[:-1]

    print_note("Save cache...")
    with open('cache.csv', 'w') as csvfile:
        cache = csv.writer(
            csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        cache.writerows(data_to_save)
