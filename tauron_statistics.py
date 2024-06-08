import argparse
from datetime import date

from dateutil import relativedelta as rd

from data_processor import (
    DataPoint, RE_RETRIEVE_RATIO, load_config, load_cache, save_cache)
from month import last_day_of_month
from table_view import TableView, Cell, CellAlignment
from tauron import login_to_tauron, gather_and_parse_data_from_tauron
from util import (
    balance_color, WIDTH, PRECISION, print_err, print_note)


def main() -> None:
    date_today = date.today()

    parser = argparse.ArgumentParser(
        description='Gather and aggregate data from Tauron eLicznik')
    parser.add_argument(
        '-y', '--year',
        dest='data_year', nargs='?', const=date_today.year, type=int,
        help='If provided, only data from selected year will be analysed.')
    parser.add_argument(
        '--no-cache',
        dest='use_cache', action='store_false', help='Don\'t use cache.'
    )
    parser.add_argument(
        '--off', '--offline', dest='offline', action='store_true',
        help='Don\'t download data from the Tauron eLicznik.'
    )
    parser.add_argument(
        '-f', '--format', nargs='?', choices=["csv", "json"],
        help="Simplify output (showing only table) and use csv or json format."
    )

    args = parser.parse_args()

    config = load_config()
    try:
        # Required:
        meter_id = config["meter_id"]
        username = config["username"]
        password = config["password"]
        installation_date = date.fromisoformat(config["installation_date"])

        # Optional:
        price_kWh = config.get("price", None)
        monthly_fixed_cost = config.get("fixed_cost", None)
    except KeyError as e:
        print_err(f"Key {e} not found in config file")
        exit(1)
    except ValueError as e:
        print_err(f"[Error] {e}")
        exit(1)

    all_data: list[DataPoint] = []
    iter_date = installation_date

    if args.data_year is not None:
        if (installation_date.year > args.data_year or
                args.data_year > date_today.year):
            print_err(
                f"Selected year must be between "
                f"{installation_date.year} and {date_today.year}")
        if args.data_year != date_today.year:
            print_note(
                "You can use offline mode, "
                "if you already have data in cache.")

        if iter_date.year < args.data_year:
            iter_date = date(args.data_year, 1, 1)

    if not args.use_cache and args.offline:
        print_note("There are no data to process. Use cache or online mode.")
        exit(0)

    if args.use_cache:
        print_note("Loading cache data...")
        cache_data = sorted(load_cache(), key=(lambda x: x.month))
        if cache_data != []:
            all_data.extend(cache_data)

            # find last date kept in cache
            last_date_in_cache = cache_data[-1].month
            iter_date = last_date_in_cache + rd.relativedelta(months=+1, day=1)

    if iter_date == date_today:
        print_note(
            "Today is the first day of the month. "
            "All available data points were loaded from cache.")
    elif not args.offline:
        session = login_to_tauron(username, password, config["extra_headers"])
        processed_data = gather_and_parse_data_from_tauron(
            session, meter_id, iter_date, date_today, installation_date,
            args.format is not None)

        if len(processed_data):
            date_of_last_dp = processed_data[-1].month + rd.relativedelta(
                day=processed_data[-1].days)

            all_data.extend(processed_data)

            print_note(f"Last day with useful data is {date_of_last_dp}")

            if args.use_cache:
                # NOTE: there is no point in saving cache,
                # if we don't get any new data
                save_cache(all_data, date_today)

    # print data
    if args.data_year is not None:
        print_note(f"# Data for {args.data_year} year only! #")

    table = TableView()
    table.set_header([
        "Date", "Usage", "kWh/day", "RE", "RE 2 use", "(+) days", "Balance"])

    totalUsage = 0.0
    totalRE = 0.0
    months = 0

    for data_point in all_data:
        dp_date = data_point.month
        usage = data_point.usage
        RE = data_point.oze
        balance = data_point.balance
        positive_days = data_point.positive_days

        # If specific year is selected skip others
        if args.data_year is not None and dp_date.year != args.data_year:
            continue

        lastDay = last_day_of_month(dp_date)
        days = lastDay.day if lastDay < date_today else date_today.day - 1

        # corner case: installation day might not be the first day of the month
        if (dp_date.month == installation_date.month and
                dp_date.year == installation_date.year):
            days -= (installation_date.day - 1)

        table.add_row([
            f"{dp_date:%Y-%m}",
            f"{usage:.{PRECISION}f}",
            f"{usage/days:.{PRECISION}f}",
            f"{RE:.{PRECISION}f}",
            f"{RE*RE_RETRIEVE_RATIO:.{PRECISION}f}",
            positive_days,
            Cell(balance, "balance", CellAlignment.RIGHT)
        ])

        totalUsage += usage
        totalRE += RE
        months += 1

    totalBalance = totalRE * RE_RETRIEVE_RATIO - totalUsage

    if price_kWh is not None and monthly_fixed_cost is not None:
        energy_cost = round(
            (-1 * totalBalance * price_kWh if totalBalance < 0 else 0.0), 2)
        fixed_cost = months * monthly_fixed_cost
        estimated_cost = energy_cost + fixed_cost

    # Print estimation for current month
    # We need at least one day of data and we don't need estimations
    # if we chose to analyse different year then current
    if dp_date.month == date_today.month and (
            args.data_year is None or date_today.year == args.data_year):

        days = last_day_of_month(date_today).day
        # we don't get todays data so we need to subtract 1 day
        ratio = days / (date_today.day - 1)

        table.add_divider()
        table.add_row([
            f"Estm-{date_today:%m}",
            f"{ratio*usage:.{PRECISION}f}",
            f"{ratio*usage/days:.{PRECISION}f}",
            f"{ratio*RE:.{PRECISION}f}",
            f"{ratio*RE*RE_RETRIEVE_RATIO:.{PRECISION}f}",
            int(ratio*positive_days),
            Cell(ratio*balance, "balance", CellAlignment.RIGHT)
        ])

    if args.format == "csv":
        print(table.to_csv())
    elif args.format == "json":
        print(table.to_json())

    if args.format is not None:
        # No summary if we want different format
        exit(0)

    print(table, end="")

    # Print summary
    print(f"> Total usage:  {totalUsage:{WIDTH}.{PRECISION}f} kWh")
    print(f"> Total RE:     {totalRE:{WIDTH}.{PRECISION}f} kWh")
    print(f"> Lost RE:      {totalRE*0.2:{WIDTH}.{PRECISION}f} kWh")
    print(f"> RE to use:    {totalRE*RE_RETRIEVE_RATIO:{WIDTH}.{PRECISION}f} kWh")
    print(f"> Balance:      {balance_color(totalBalance, WIDTH, 'kWh')}")

    if price_kWh is None or monthly_fixed_cost is None:
        exit()
    print(f"> Estim. cost:  {estimated_cost:{WIDTH}.{PRECISION}f} PLN (fix. {fixed_cost:.{PRECISION}f} PLN)")


if __name__ == "__main__":
    main()
