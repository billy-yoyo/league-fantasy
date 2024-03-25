import requests
from bs4 import BeautifulSoup
import urllib.parse
from ..models import Team, Player
from .score_calculator import calculate_score

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"

def get_or_create_player(team, player_id, position, tournament, season):
  url = f"https://gol.gg/players/player-stats/{player_id}/{season}/split-ALL/tournament-{urllib.parse.quote(tournament)}/champion-ALL/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")
  title = soup.find("h1").get_text().strip()

  country = ""
  country_img = soup.select_one("h1 img")
  if country_img and country_img.has_attr("alt"):
    country = country_img.get("alt").strip()

  try:
    player = Player.objects.get(player_id=player_id)
    player.in_game_name = title
    player.team = team
    player.country = country
    player.position = position
  except:
    player = Player(in_game_name=title, team=team, player_id=player_id, country=country, position=position, score=0)

  player.save()

  return player


def get_or_create_team(team_id, tournament):
  url = f"https://gol.gg/teams/team-stats/{team_id}/split-ALL/tournament-{urllib.parse.quote(tournament)}/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")
  title = soup.find("h1").get_text().strip()
  short_name = title[:3].upper()

  for item in soup.select("td.p-1.text-blue"):
    item_text = item.get_text().strip().lower()
    if item_text != "blue side" and item_text.endswith("blue side"):
      short_name = item_text[:-10].strip().upper()
  
  try:
    team = Team.objects.get(team_id=team_id)
    team.full_name = title
    team.short_name = short_name
  except:
    team = Team(full_name=title, short_name=short_name, team_id=team_id, icon_url="")
  
  team.save()
  
  players = []
  positions = ["top", "jungle", "mid", "bot", "support"]
  for link in soup.select("table tr a"):
    href = link.get("href")
    if href and href.startswith("../players"):
      parts = href.split("/")
      player_id = parts[3]
      season_name = parts[4]
      position = positions.pop(0)
      players.append(get_or_create_player(team, player_id, position, tournament, season_name))
  
  return [team, players]

def get_teams_and_players(tournament):
  teams = []
  players = []
  url = f"https://gol.gg/tournament/tournament-ranking/{urllib.parse.quote(tournament)}/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")
  for link in soup.select("table tr a"):
    href = link.get("href")
    if href and href.startswith("../teams"):
      parts = href.split("/")
      team_id = parts[3]
      [team, team_players] = get_or_create_team(team_id, tournament)
      teams.append(team)
      players += team_players

  return [teams, players]


