import os
from datetime import datetime

import requests
import rich_click as click
from bs4 import BeautifulSoup
from bs4.element import Tag

from .output import output_table


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


def gfl_upcoming_games(tag: Tag) -> bool:
    """Check if the game is upcomping"""
    if not is_gfl_game(tag):
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


def gfl_games_today(tag: Tag) -> bool:
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


def get_data() -> Tag:
    """
    Fetch and parse the GFL schedule.

    The schedule will be updated every 15 minutes. So the file should only be
    loaded when the local copy is older than that.
    See: https://www.afvd.de/xml-export-von-daten/
    """
    schedule_filename = "spielplan.xml"
    gfl_schedule_url = "http://vereine.football-verband.de/spielplan.xml"  # noqa

    if should_schedule_be_refeshed("spielplan.xml"):
        click.echo("Schedule is old. Downloading again.")

        response = requests.get(gfl_schedule_url)

        if response.status_code == 200:
            with open(schedule_filename, "w") as f:
                f.write(response.text)
    else:
        click.echo("Schedule seems fresh. Using local copy.")

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
def todays_games(format):
    """Output every GFL game played today."""
    data = get_data()
    upcoming_games = data.find_all(gfl_games_today)

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
def upcoming_games(format):
    """Output every upcoming GFL game."""
    data = get_data()

    upcoming_games = data.find_all(gfl_upcoming_games)

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
