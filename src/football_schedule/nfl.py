from datetime import datetime

import nfl_data_py as nfl
import pytz
import rich_click as click

from .output import output_table


@click.command()
@click.option(
    "--format",
    "-f",
    default="table",
    show_default=True,
    help="The output format.",
)
def seattle_games(format):
    df = nfl.import_schedules([2022])

    seattle_games = df[df["game_id"].str.contains("SEA")]

    gamedays = seattle_games["gameday"]
    gametime = seattle_games["gametime"]
    home_teams = seattle_games["home_team"]
    away_teams = seattle_games["away_team"]

    if format == "table":
        headers = ["Datum", "Kickoff", "Heim", "Gast"]
        rows = list()

    for index in home_teams.index:
        input_str = f"{gamedays[index]} {gametime[index]} -0400"
        game_date = datetime.strptime(input_str, "%Y-%m-%d %H:%M %z")
        game_date = game_date.astimezone(pytz.timezone("Europe/Berlin"))

        game_date_str = game_date.strftime("%d.%m.%Y")
        kickoff = game_date.strftime("%H:%M")
        rows.append(
            [
                game_date_str,
                f"{kickoff} Uhr",
                home_teams[index],
                away_teams[index],
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
def upcoming_seattle_games(format):
    df = nfl.import_schedules([2022])

    seattle_games = df[df["game_id"].str.contains("SEA")]
    today = str(datetime.today())
    upcoming_games = seattle_games[seattle_games["gameday"] > today]

    gamedays = upcoming_games["gameday"]
    gametime = upcoming_games["gametime"]
    home_teams = upcoming_games["home_team"]
    away_teams = upcoming_games["away_team"]

    if format == "table":
        headers = ["Datum", "Kickoff", "Heim", "Gast"]
        rows = list()

    for index in home_teams.index:
        date_str = f"{gamedays[index]} {gametime[index]} -0400"
        game_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M %z")
        game_date = game_date.astimezone(pytz.timezone("Europe/Berlin"))

        game_date_str = game_date.strftime("%d.%m.%Y")
        kickoff = game_date.strftime("%H:%M")
        rows.append(
            [
                game_date_str,
                f"{kickoff} Uhr",
                home_teams[index],
                away_teams[index],
            ]
        )

    output_table(headers, rows)
