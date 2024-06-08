# NOTE: I tried a few different libraries to do this
# but non of them works exactly as I want to, so ...
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


class TableView():
    _headers: list[str] = []
    _rows: list[list[Any]] = []

    def __init__(self, col_width: int = 8) -> None:
        self.width = col_width

    def __str__(self) -> str:
        out = ""
        for h in self._headers:
            out += f"| {h:<{self.width}} "
        out += "|\n"

        length = len(out) - 1
        line = "-" * length + "\n"

        out = line + out
        out += line

        for row in self._rows:
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
        self._rows.append(row)

    def add_divider(self) -> None:
        self._rows.append(LINE)

    def set_header(self, header: list[Any], config: Any = None) -> None:
        self._headers = header
        # TODO: header configuration
