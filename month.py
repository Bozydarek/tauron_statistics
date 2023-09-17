from datetime import date
from dateutil import relativedelta as rd


def last_day_of_month(any_day: date) -> date:
    return any_day + rd.relativedelta(day=1, months=+1, days=-1)


def months_between(date1: date, date2: date) -> int:
    # NOTE: I used simple math instead of rd.relativedelta(date1, date2)
    # because I don't care how many months would "fit" between date1 and date2
    # For example both for date1 = 2020-01-30 and date2 = 2020-02-02 as for
    # date1 = 2020-01-01 and date2 = 2020-02-28 this function will return 1
    return abs((date1.year - date2.year) * 12 + date1.month - date2.month)
