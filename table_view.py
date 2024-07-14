# NOTE: I tried a few different libraries to do this
# but non of them works exactly as I want to, so ...
import csv
import json

from io import StringIO
from enum import Enum
from dataclasses import dataclass

from typing import Any

from util import Color, balance_color, PRECISION

LINE = ["---"]


class CellAlignment(Enum):
    LEFT = "<"
    RIGHT = ">"


@dataclass
class Cell():
    content: Any
    color: Color | str | None = None
    alignment: CellAlignment = CellAlignment.LEFT
    width: int | None = None

    def __str__(self) -> str:
        # NOTE: used for json and csv format
        return str(self.content)


class TableView():
    headers: list[tuple[str, str]] = []
    rows: list[list[Any]] = []

    def __init__(self, col_width: int = 8) -> None:
        self.width = col_width

    def __str__(self) -> str:
        out = ""
        for h in self.get_header():
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

            for i, cell in enumerate(row):
                if type(cell) is not Cell:
                    alignment = (CellAlignment.LEFT if i == 0
                                 else CellAlignment.RIGHT)
                    cell = Cell(cell, alignment=alignment)

                value = cell.content
                width = self.width if cell.width is None else cell.width

                if type(cell.color) is Color:
                    value = f"{cell.color}{value}{Color.END}"
                    width += len(value) - len(str(cell.content))

                elif cell.color == "balance":
                    value = balance_color(cell.content)
                    num_width = len(f"{cell.content:.{PRECISION}f}")
                    width += len(value) - num_width

                out += f"| {value:{cell.alignment.value}{width}} "

            out += "|\n"

        out += line

        return out

    def add_row(self, row: list[Any] = []) -> None:
        self.rows.append(row)

    def add_divider(self) -> None:
        self.rows.append(LINE)

    def set_header(self, header: list[tuple[str, str]],
                   config: Any = None) -> None:
        self.headers = header
        # TODO: header configuration

    def get_header(self, id_mode: bool = False) -> list[str]:
        if id_mode:
            return [header[0] for header in self.headers]
        return [header[1] for header in self.headers]

    def to_json(self) -> str:
        return json.dumps(
            [dict(zip(self.get_header(True), map(str, row)))
             for row in self.rows
             if row != LINE],
            indent=4)

    def to_csv(self) -> str:
        output = StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(self.get_header(True))
        for row in self.rows:
            if row != LINE:
                writer.writerow(map(str, row))

        return output.getvalue()
