from typing import Dict, List

from rich.console import Console
from rich.table import Table

console = Console()


def output_table(headers: List, rows: List) -> None:
    """Optput table to console.

    :param headers: The table headers
    :param rows: The table rows
    """
    table = Table(show_header=True, header_style="bold magenta")

    for header in headers:
        table.add_column(header)

    for row in rows:
        table.add_row(*row)

    console.print(table)


def inkplate_file_content(game: Dict, league: str) -> str:
    """File content for game object

    :param game: The game to convert.

    :return: str
    """
    date = game["date"].strftime("%A, %d.%m.%Y")
    kickoff = game["date"].strftime("%H:%M")

    file_content = "\n".join(
        [
            game["home_team"].lower(),
            game["away_team"].lower(),
            date,
            f"{kickoff} Uhr",
            f"{league}",
        ]
    )

    return file_content
