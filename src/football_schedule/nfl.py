import locale
from datetime import datetime
from typing import Dict

import pytz
import requests
import rich_click as click

from .output import output_table

try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "de_DE")
    except locale.Error as e:
        raise e


def get_season_year() -> int:
    """Return the year for the season with upcoming games

    :returns: The year as an integer
    """
    now = datetime.now()
    current_year = now.year

    if now.month < 3:
        return current_year - 1

    return current_year


def fetch_seattle_games(season_type: str = "reg") -> Dict:
    """Fetch the games for the given season type

    :param season_type: The season type, either pre, reg or post

    :returns: The response json as dict
    """
    season_types = {"pre": 1, "reg": 2, "post": 3}
    season_type_id = season_types[season_type]
    season_year = get_season_year()

    url = (
        "https://site.web.api.espn.com/apis/site/v2/sports/football/"
        f"nfl/teams/sea/schedule?region=us&lang=en&season={season_year}&"
        f"seasontype={season_type_id}"
    )

    res = requests.get(url)

    if res.status_code == 200:
        return res.json()


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
@click.pass_context
def seattle_games(ctx, format, team_name_format):
    pre_season_games = fetch_seattle_games("pre")["events"]
    regular_season_games = fetch_seattle_games("reg")["events"]
    post_season_games = fetch_seattle_games("post")["events"]

    games = pre_season_games + regular_season_games + post_season_games

    rows = list()

    for game in games:
        input_str = game["date"]
        game_date = datetime.strptime(input_str, "%Y-%m-%dT%H:%M%z")
        game_date = game_date.astimezone(pytz.timezone("Europe/Berlin"))

        game_date_str = game_date.strftime("%d.%m.%Y")
        kickoff = game_date.strftime("%H:%M")

        teams = game["competitions"][0]["competitors"]

        for team in teams:
            if team["homeAway"] == "home":
                if team_name_format == "abbreviation":
                    home_team = team["team"]["abbreviation"]
                else:
                    home_team = team["team"]["displayName"]

            if team["homeAway"] == "away":
                if team_name_format == "abbreviation":
                    away_team = team["team"]["abbreviation"]
                else:
                    away_team = team["team"]["displayName"]

        if format == "list":
            rows.append(
                {
                    "date": game_date,
                    "away_team": away_team,
                    "home_team": home_team,
                }
            )

        if format == "table":
            rows.append(
                [
                    game_date_str,
                    f"{kickoff} Uhr",
                    home_team,
                    away_team,
                ]
            )

    if format == "list":
        return rows

    if format == "table":
        headers = ["Datum", "Kickoff", "Heim", "Gast"]

        output_table(headers, rows)


@click.command()
@click.option(
    "--format",
    "-f",
    default="table",
    show_default=True,
    help="The output format.",
)
@click.pass_context
def upcoming_seattle_games(ctx, format):
    rows = list()
    games = ctx.invoke(seattle_games, format="list")

    tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(tz)

    if format == "table":
        headers = ["Datum", "Kickoff", "Heim", "Gast"]

    for game in games:
        if game["date"] > now:
            date = game["date"].strftime("%d.%m.%Y")
            kickoff = game["date"].strftime("%H:%M")
            rows.append(
                [
                    date,
                    f"{kickoff} Uhr",
                    game["home_team"],
                    game["away_team"],
                ]
            )

    output_table(headers, rows)


@click.command()
@click.argument("output_file", type=click.File("w"))
@click.pass_context
def upcoming_seattle_game_file(ctx, output_file):
    games = ctx.invoke(
        seattle_games,
        format="list",
        team_name_format="abbreviation",
    )

    tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(tz)

    game_to_return = None

    for game in games:
        if game["date"] > now:
            game_to_return = game
            break
    else:
        # When there's not future game scheduled, return and do nothing
        return

    date = game_to_return["date"].strftime("%A, %d.%m.%Y")
    kickoff = game_to_return["date"].strftime("%H:%M")

    file_content = game_to_return["home_team"].lower() + "\n"
    file_content += game_to_return["away_team"].lower() + "\n"
    file_content += date + "\n"
    file_content += f"{kickoff} Uhr"

    output_file.write(file_content)
