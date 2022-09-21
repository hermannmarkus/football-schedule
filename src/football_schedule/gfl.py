import os
from datetime import datetime

import requests
import rich_click as click
from bs4 import BeautifulSoup
from bs4.element import Tag
from rich.console import Console

from .output import output_table

console = Console()


def is_gfl_game(tag: Tag) -> bool:
    """Check if the game tag is from the GFL"""
    return bool(tag.find("Liga", string="GFL"))


def filter_marburg_gfl_games(tag: Tag) -> bool:
    """Check if the home or guest team is the mercenaries"""
    if is_gfl_game(tag) is False:
        return False

    if tag.find("Heim", string="Marburg Mercenaries"):
        return True

    if tag.find("Gast", string="Marburg Mercenaries"):
        return True

    return False


def filter_upcoming_mercenaries_games(tag: Tag) -> bool:
    """Check if the game is upcoming and from the mercenaries."""
    is_marburg_game = filter_marburg_gfl_games(tag)
    is_upcoming = filter_upcoming_games(tag)

    if is_marburg_game is True and is_upcoming is True:
        return True

    return False


def filter_upcoming_games(tag: Tag) -> bool:
    """Check if the game is upcomping"""
    if is_gfl_game(tag) is False:
        return False

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
    if not tag.find("Liga", string="GFL"):
        return False

    if tag.find("Datum2").string != "0000-00-00":
        return False

    game_date_str = tag.find("Datum1").string
    game_date = datetime.strptime(game_date_str, "%Y-%m-%d")
    delta = datetime.now() - game_date

    if delta.days == 0:
        return True


def should_schedule_be_refeshed(filename: str) -> bool:
    """Check if the file is older than 15 minutes"""
    st = os.stat(filename)
    mtime = st.st_mtime
    schedule_age = datetime.fromtimestamp(mtime)

    delta = datetime.now() - schedule_age
    delta_minutes = delta.total_seconds() / 60

    if delta_minutes > 15:
        return True


def get_data(ctx: click.core.Context) -> Tag:
    """
    Fetch and parse the GFL schedule.

    The schedule will be updated every 15 minutes. So the file should only be
    loaded when the local copy is older than that.
    See: https://www.afvd.de/xml-export-von-daten/
    """
    schedule_filename = "spielplan.xml"
    gfl_schedule_url = "http://vereine.football-verband.de/spielplan.xml"  # noqa

    if should_schedule_be_refeshed("spielplan.xml"):
        if ctx.obj["debug"]:
            console.log("Schedule is old. Downloading again.")

        response = requests.get(gfl_schedule_url)

        if response.status_code == 200:
            with open(schedule_filename, "w") as f:
                f.write(response.text)
    else:
        if ctx.obj["debug"]:
            console.log("Schedule seems fresh. Using local copy.")

    with open(schedule_filename, "r") as file:
        content = file.read()

    soup = BeautifulSoup(content, features="xml")
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
    upcoming_games = data.find_all(filter_games_today)

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

    upcoming_games = data.find_all(filter_upcoming_games)

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
                    game.Gast.string,
                    game.Heim.string,
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
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def upcoming_mercenaries_games(ctx, format, debug):
    """Output every upcoming GFL game."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    data = get_data(ctx)

    upcoming_games = data.find_all(filter_upcoming_mercenaries_games)

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
                    game.Gast.string,
                    game.Heim.string,
                    game.Gruppe.string,
                )
            )

        output_table(headers, rows)
