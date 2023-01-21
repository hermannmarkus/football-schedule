from datetime import datetime

import requests
import rich_click as click
from bs4 import BeautifulSoup
from bs4.element import Tag
from rich.console import Console

from .output import output_table

console = Console()


def fixed_string(input: str) -> str:
    """Replace the wrong umlaut markup and replace it by the
    actual utf-8 characters

    :param input: The input string

    :returns: The string with the replaced characters.
    """
    text = (
        input.replace("&#xC3;&#xA4;", "ä")
        .replace("&#xC3;&#x84;", "Ä")
        .replace("&#xC3;&#x96;", "Ö")
        .replace("&#xC3;&#xB6;", "ö")
        .replace("&#xC3;&#xBC;", "ü")
        .replace("&#xC3;&#x9C;", "Ü")
        .replace("&#xC3;&#x9F;", "ß")
    )

    return text


def filter_marburg_games(tag: Tag) -> bool:
    """Check if the home or guest team is the mercenaries"""
    if tag.find("Heim", string="Marburg Mercenaries"):
        return True

    if tag.find("Gast", string="Marburg Mercenaries"):
        return True

    return False


def filter_upcoming_mercenaries_games(tag: Tag) -> bool:
    """Check if the game is upcoming and from the mercenaries."""
    is_marburg_game = filter_marburg_games(tag)
    is_upcoming = filter_upcoming_games(tag)

    if is_marburg_game is True and is_upcoming is True:
        return True

    return False


def filter_upcoming_games(tag: Tag) -> bool:
    """Check if the game is upcomping"""

    # If there is a possible second date it is assumed the
    # game is in the future.
    if tag.find("Datum2").string != "0000-00-00":
        return True

    game_date_str = tag.find("Datum1").string
    game_date = datetime.strptime(game_date_str, "%Y-%m-%d")

    delta = datetime.now() - game_date

    if delta.days < 1:
        return True


def filter_games_today(tag: Tag) -> bool:
    """Check if the game will take place the same day"""
    if tag.find("Datum2").string != "0000-00-00":
        return False

    game_date_str = tag.find("Datum1").string
    game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
    delta = datetime.now() - game_date

    if delta.days == 0:
        return True


def get_data(ctx: click.core.Context) -> Tag:
    """Fetch and parse the GFL schedule."""
    gfl_schedule_url = (
        "https://vereine.football-verband.de/xmlspielplan.php5?" "Liga=GFL"
    )

    response = requests.get(gfl_schedule_url)

    soup = BeautifulSoup(fixed_string(response.text), features="xml")

    tabelle = soup.tabelle

    return tabelle


@click.command()
@click.option(
    "--format",
    "-f",
    default="table",
    show_default=True,
    help="The output format.",
)
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def todays_games(ctx, format, debug):
    """Output every GFL game played today."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    data = get_data(ctx)
    upcoming_games = data.find_all(filter_games_today, recursive=False)

    if format == "table":
        headers = ["Kickoff", "Heim", "Gast"]
        rows = list()

        for game in upcoming_games:
            home = game.heim.string
            guest = game.gast.string
            kickoff = game.kickoff.string

            rows.append(
                [
                    f"{kickoff} Uhr",
                    home,
                    guest,
                ]
            )

        output_table(headers, rows)


@click.command()
@click.option(
    "--format",
    "-f",
    default="table",
    show_default=True,
    help="The output format.",
)
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def upcoming_games(ctx, format, debug):
    """Output every upcoming GFL game."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    data = get_data(ctx)

    upcoming_games = data.find_all(filter_upcoming_games, recursive=False)

    if format == "table":
        headers = ["Datum", "Kickoff", "Heim", "Gast", "Gruppe"]
        rows = list()

        for game in upcoming_games:
            game_date_str_1 = game.Datum1.string
            game_date_str_2 = game.Datum2.string
            game_date_1 = datetime.strptime(game_date_str_1, "%Y-%m-%d")

            game_date = game_date_1.strftime("%d.%m.%Y")

            if game_date_str_2 != "0000-00-00":
                game_date_2 = datetime.strptime(game_date_str_2, "%Y-%m-%d")

                game_date += " / " + game_date_2.strftime("%d.%m.%Y")

            kickoff = game.Kickoff.string

            rows.append(
                (
                    game_date,
                    f"{kickoff} Uhr",
                    game.Heim.string,
                    game.Gast.string,
                    game.Gruppe.string,
                )
            )

        output_table(headers, rows)


@click.command()
@click.option(
    "--format",
    "-f",
    default="table",
    show_default=True,
    help="The output format.",
)
@click.option(
    "--team-name-format",
    default="displayName",
    show_default=True,
    help="The output format of the team names.",
)
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def upcoming_mercenaries_games(ctx, format, team_name_format, debug):
    """Output every upcoming GFL game."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    data = get_data(ctx)

    upcoming_games = data.find_all(
        filter_upcoming_mercenaries_games,
        recursive=False,
    )

    if format == "list":
        games = list()

        for game in upcoming_games:
            game_date = f"{game.Datum1.string} {game.Kickoff.string}+02:00"
            game_date = datetime.strptime(game_date, "%Y-%m-%d %H:%M%z")

            if team_name_format == "abbreviation":
                home = game.Heimkuerzel.string
                away = game.Gastkuerzel.string
            else:
                home = game.Heim.string
                away = game.Gast.string

            games.append(
                {
                    "date": game_date,
                    "home_team": home,
                    "away_team": away,
                }
            )

        games = sorted(games, key=lambda d: d["date"])

        return games

    if format == "table":
        headers = ["Datum", "Kickoff", "Heim", "Gast", "Gruppe"]
        rows = list()

        for game in upcoming_games:
            game_date_str_1 = game.Datum1.string
            game_date_str_2 = game.Datum2.string
            game_date_1 = datetime.strptime(game_date_str_1, "%Y-%m-%d")

            game_date = game_date_1.strftime("%d.%m.%Y")

            if game_date_str_2 != "0000-00-00":
                game_date_2 = datetime.strptime(game_date_str_2, "%Y-%m-%d")

                game_date += " / " + game_date_2.strftime("%d.%m.%Y")

            kickoff = game.Kickoff.string

            rows.append(
                (
                    game_date,
                    f"{kickoff} Uhr",
                    game.Heim.string,
                    game.Gast.string,
                    game.Gruppe.string,
                )
            )

        output_table(headers, rows)
