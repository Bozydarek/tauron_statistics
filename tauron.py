from datetime import date

import simplejson
import requests
from dateutil import relativedelta as rd

from data_processor import DataTypes, MonthlyData, DataPoint
from month import months_between, last_day_of_month
from util import print_wrn, print_err

LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
ELICZNIK_URL = "https://elicznik.tauron-dystrybucja.pl"
DATA_API_URL = f"{ELICZNIK_URL}/energia/api"

HEADERS = {
    'cache-control': "no-cache",
}


def login_to_tauron(
        username: str, password: str,
        extra_headers: list[dict[str, str]]) -> requests.sessions.Session:
    payload_login = {
        "username": username,
        "password": password,
        "service": ELICZNIK_URL,
    }

    for eh in extra_headers:
        if "name" not in eh and "value" not in eh:
            print_wrn(f"Wrong extra header configuration: {eh}")
            continue
        HEADERS[eh["name"]] = eh["value"]

    print("Starting session...")
    # NOTE: Login service require two requests for some reason
    session = requests.Session()
    p1 = session.request(
        "POST", LOGIN_URL, data=payload_login, headers=HEADERS)
    p2 = session.request(
        "POST", LOGIN_URL, data=payload_login, headers=HEADERS)

    if p1.status_code != 200 or p2.status_code != 200:
        print_err(
            "There were some problems with logging to Tauron eLicznik service")
        exit(1)

    return session


def gather_and_parse_data_from_tauron(
        session: requests.sessions.Session,
        meter_id: str,
        iter_date: date,
        date_today: date,
        installation_date: date) -> list[DataPoint]:
    # if date_today > iter_date we will gather additional month (current)
    # otherwise it's mean that date_today == iter_date (1st day of month)
    months_to_gather = (
        months_between(date_today, iter_date) +
        int(date_today > iter_date) - int(date_today.day == 1))

    print(
        f"Gathering data for {months_to_gather} "
        f"month{'s' if months_to_gather > 1 else ''}... ")
    print("[", end='', flush=True)
    data: list[DataPoint] = []
    while (iter_date < date_today):
        # NOTE: "new API" specification:
        # from, to - dates in format %-d.%m.%Y (days w/o leading zero)
        # type - oze or consum - for energy send and taken from the grid
        # profile - year, month, full+time - for year / month / day date

        eng_data: dict[DataTypes, MonthlyData] = {}
        for eng_type in DataTypes:
            body = {
                "from": iter_date.strftime("%-d.%m.%Y"),
                "to": last_day_of_month(iter_date).strftime("%-d.%m.%Y"),
                "type": str(eng_type),
                "profile": "month",
            }

            response = session.request(
                "POST", DATA_API_URL, data=body, headers=HEADERS)

            if response.status_code != 200:
                print_err(
                    f"HTTP {response.status_code} status code returned"
                    f"while getting {eng_type} data for "
                    f"{iter_date.isoformat()}")
            else:
                # try to parse data
                try:
                    eng_data[eng_type] = MonthlyData.parseData(
                        eng_type, iter_date, response.json()["data"])
                except simplejson.JSONDecodeError as e:
                    print_err(
                        f"JSON Decode Error: {e} for {iter_date.isoformat()}")

        data.append(DataPoint.fromMonthlyData(
            eng_data[DataTypes.consume],
            eng_data[DataTypes.oze],
            installation_date))

        iter_date += rd.relativedelta(months=+1, day=1)
        print(".", end='', flush=True)
    print("]")

    return data
