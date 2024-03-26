import requests
from bs4 import BeautifulSoup
import urllib.parse
from ..models import Team, Player, PlayerStat, Game, Tournament, PlayerSynonym
from .stats import STAT_MATCHERS

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"

def get_stat(name):
  for stat in STAT_MATCHERS:
    if stat.matches(name):
      return stat
  return None

def find_all_game_stats(soup, player_ids):
  print(player_ids)
  player_stats = {pid: {} for pid in player_ids}

  for row in soup.select("table.completestats tr"):
    data = list(row.find_all("td"))
    if data:
      stat = get_stat(data[0].get_text().lower().strip())
      if stat:
        for entry, player_id in zip(data[1:], player_ids):
          value_text = entry.get_text().replace("%", "").strip()
          try:
            if value_text.lower() == "perfect kda":
              value = 999
            elif not value_text:
              value = 0
            else:
              value = float(value_text)
            player_stats[player_id][stat.name] = value
          except:
            pass
      else:
        print(f"no matching stat for {data[0].get_text()}")
  
  return player_stats

def get_game_teams(game_id, tournament, recurse):
  teams = []
  url = f"https://gol.gg/game/stats/{game_id}/page-game/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")
  winner = None
  for link in soup.select("a:not(.nav-link)"):
    href = link.get("href")
    if href and href.startswith("../teams"):
      parts = href.split("/")
      team_id = parts[3]
      won = link.parent.get_text().strip().lower().endswith("win")
      try:
        team = Team.objects.get(team_id=team_id)
        teams.append(team)
        if won:
          winner = team.team_id
      except:
        pass
  
  other_game_ids = []
  if recurse:
    # check if this is a best-of series
    for link in soup.select("a.nav-link"):
      href = link.get("href")
      if href and href.startswith("../game") and href.endswith("/page-game/"):
        parts = href.split("/")
        other_game_id = parts[3]
        if game_id != other_game_id and not Game.objects.filter(game_id=other_game_id).exists():
          other_game_ids.append(other_game_id)
  return teams, other_game_ids, winner

def get_game(game_id, tournament, recurse):
  teams, other_game_ids, winner = get_game_teams(game_id, tournament, recurse)
  if len(teams) != 2:
    raise Exception(f"didn't find 2 teams: {', '.join(str(x) for x in teams)}")

  game = Game(game_id=game_id, team_a=teams[0], team_b=teams[1], tournament=tournament, winner=winner)
  game.save()

  for other_game_id in other_game_ids:
    get_game_and_stats(other_game_id, tournament, False)

  return game

def get_game_and_stats(game_id, tournament, recurse=True):
  try:
    game = Game.objects.get(game_id=game_id)
  except:
    game = get_game(game_id, tournament, recurse)

  url = f"https://gol.gg/game/stats/{game_id}/page-fullstats/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")

  players = []

  for row in soup.select("table.completestats tr"):
    data = list(row.find_all("td"))
    if data and data[0].get_text().strip().lower() == "player":
      for entry in data[1:]:
        player_name = entry.get_text().strip()
        try:
          player_synonym = PlayerSynonym.objects.get(name__iexact=player_name)
          players.append(player_synonym.player)
        except:
          print(f"failed to find player with name {player_name}")

  player_stats = find_all_game_stats(soup, [p.player_id for p in players])
  print(player_stats)
  for player in players:
    stats = player_stats[player.player_id]
    for key, value in stats.items():
      player_stat = PlayerStat(player=player, game=game, stat_name=key, stat_value=value)
      player_stat.save()

def get_missing_games(tournament):
  missing_game_ids = []
  url = f"https://gol.gg/tournament/tournament-matchlist/{urllib.parse.quote(tournament)}/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")

  for link in soup.select("a:not(.nav-link)"):
    href = link.get("href")
    if href and href.startswith("../game"):
      parts = href.split("/")
      game_id = parts[3]
      if not Game.objects.filter(game_id=game_id).exists():
        missing_game_ids.append(game_id)
  return missing_game_ids

def update_game_data_for_tournament(tournament):
  for game_id in get_missing_games(tournament.name):
    get_game_and_stats(game_id, tournament)

def refresh_game_data_for_tournament(tournament):
  for game in Game.objects.filter(tournament__name=tournament.name):
    get_game_and_stats(game.game_id, tournament)

def update_game_data_for_season(season):
  for tournament in Tournament.objects.filter(season=season):
    update_game_data_for_tournament(tournament)

def refresh_game_data_for_season(season):
  for tournament in Tournament.objects.filter(season=season):
    refresh_game_data_for_tournament(tournament)
