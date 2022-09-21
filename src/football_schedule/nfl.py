from datetime import datetime

import pytz
import requests
import rich_click as click

from .output import output_table


def fetch_seattle_games() -> dict:
    res = requests.get(
        (
            "https://site.web.api.espn.com/apis/site/v2/sports/football/"
            "nfl/teams/sea/schedule?region=us&lang=en&season=2022&seasontype=2"
        )
    )

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
@click.pass_context
def seattle_games(ctx, format):
    games = fetch_seattle_games()["events"]

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
                home_team = team["team"]["displayName"]

            if team["homeAway"] == "away":
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
