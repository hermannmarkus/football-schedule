import rich_click as click

from .gfl import upcoming_mercenaries_games
from .nfl import upcoming_seattle_games
from .output import inkplate_file_content


@click.command()
@click.argument("output_file", type=click.File("w"))
@click.pass_context
def upcoming_game_file(ctx, output_file):
    """Write the next football game to file.

    Only games from Marburg or Seattle are of interrest here.

    :param output: The output file to write to
    """
    content = None
    next_nfl_game = None
    next_gfl_game = None

    nfl_games = ctx.invoke(
        upcoming_seattle_games, format="list", team_name_format="abbreviation"
    )

    if nfl_games:
        next_nfl_game = nfl_games[0]

    gfl_games = ctx.invoke(
        upcoming_mercenaries_games,
        format="list",
        team_name_format="abbreviation",
    )

    if gfl_games:
        next_gfl_game = gfl_games[0]

    if next_gfl_game is None and next_nfl_game is None:
        return

    if next_gfl_game is not None and next_nfl_game is not None:
        if next_gfl_game["date"] > next_nfl_game["date"]:
            content = inkplate_file_content(next_nfl_game, "nfl")
        else:
            content = inkplate_file_content(next_gfl_game, "gfl")
    else:
        if next_gfl_game:
            content = inkplate_file_content(next_gfl_game, "gfl")

        if next_nfl_game:
            content = inkplate_file_content(next_nfl_game, "nfl")

    if content:
        output_file.write(content)
