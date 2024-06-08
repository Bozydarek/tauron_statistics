# NOTE: I tried a few different libraries to do this
# but non of them works exactly as I want to, so ...
from enum import Enum
from dataclasses import dataclass

from typing import Any

from util import bColors, color_balance, PRECISION

LINE = ["---"]


class CellAligment(Enum):
    LEFT = "<"
    RIGHT = ">"


@dataclass
class Cell():
    content: Any
    color: bColors | str | None = None
    alignment: CellAligment = CellAligment.LEFT
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
                if type(cell) is Cell:
                    value = cell.content
                    width = self.width if cell.width is None else cell.width
                    # TODO: Change bColors into Enum to support this case
                    # if type(cell.color) is bColors:
                    #     value = f"{cell.color}{value}{bColors.END}"
                    #     print(cell.color, value)
                    #     width += len(value) - len(str(cell.content))
                    if cell.color == "balance":
                        value = color_balance(cell.content)
                        num_width = len(f"{cell.content:.{PRECISION}f}")
                        width += len(value) - num_width
                    out += f"| {value:{cell.alignment.value}{width}} "
                else:
                    # TODO: Refactor this part
                    if i == 0:
                        out += f"| {cell:<{self.width}} "
                    else:
                        out += f"| {cell:>{self.width}} "

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
