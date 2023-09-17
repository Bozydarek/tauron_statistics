# NOTE: I tried a few different libraries to do this
# but non of them works exactly as I want to, so ...
from typing import Any

LINE = ["---"]


class TableView():
    headers: list[str] = []
    rows: list[list[Any]] = []
    width: int = 8

    def __str__(self) -> str:
        out = ""
        for h in self.headers:
            out += f"| {h:<{self.width}} "
        out += "|\n"

        length = len(out) - 1
        line = "-" * length + "\n"

        out = line + out
        out += line

        for row in self.rows:
            if row == LINE:
                out += line
                continue

            for i, o in enumerate(row):
                # TODO: Move this logic to some row configuration
                if i == 0:
                    out += f"| {o:<{self.width}} "
                else:
                    out += f"| {o:>{self.width}} "
            out += "|\n"

        out += line

        return out

    def add_row(self, row: list[Any] = []) -> None:
        self.rows.append(row)

    def add_divider(self) -> None:
        self.rows.append(LINE)
