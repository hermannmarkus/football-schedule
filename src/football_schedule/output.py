from typing import List

from rich.console import Console
from rich.table import Table

console = Console()


def output_table(headers: List, rows: List) -> None:
    table = Table(show_header=True, header_style="bold magenta")

    for header in headers:
        table.add_column(header)

    for row in rows:
        table.add_row(*row)

    console.print(table)
