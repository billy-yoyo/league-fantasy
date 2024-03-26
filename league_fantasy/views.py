from django.http import HttpResponse
from .scraper.scrape_teams import get_teams_and_players_for_tournament

TOURNAMENT = "LEC Spring Season 2024"

def refresh_teams_and_players(request):
    [teams, players] = get_teams_and_players_for_tournament(TOURNAMENT)

    lines = []
    lines.append("<h2>Teams:</h2><ul>")
    for team in teams:
        lines.append(f"<li>{team.team_id}, {team.full_name}, {team.short_name}</li>")

    lines.append("</ul>")
    lines.append("<h2>Players:</h2><ul>")
    for player in players:
        lines.append(f"<li>{player.player_id}, {player.in_game_name}, {player.country}, {player.position}, {player.score}</li>")
    lines.append("</ul>")

    return HttpResponse("\n".join(lines))

def refresh_matches(request):
    return HttpResponse("Done")

