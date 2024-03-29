import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..models import Team, Game

MATCH_UTC_FORMAT = "%a %Y-%m-%d %H:%M"

MATCH_ROW_REQUIRED_FIELDS = [
  "team1",
  "team2",
  "blue",
  "red",
  "rpgid",
  "w",
  "utc"
]

def is_int(x):
  try:
    int(x)
    return True
  except:
    return False

def get_or_create_team(full_name, short_name):
  team = Team.objects.filter(full_name__iexact=full_name).first()
  if not team:
    team = Team(full_name=full_name, short_name=short_name)
    team.save()
  return team

def scrape_match_list(tournament):
  tournament_name = tournament.name
  season_name = tournament.season.name

  games = []

  resp = requests.get(f"https://lol.fandom.com/wiki/Data:LEC/{season_name}/{tournament_name}")
  soup = BeautifulSoup(resp.text, "lxml")
  current_headers = []
  cached_entries = []
  cache_duration = 0
  for row in soup.select(".page-content table.wikitable tr"):
    headers = row.find_all("th")
    if len(headers) > 1:
      current_headers = [th.get_text().strip().lower() for th in headers]
      continue
    elif len(headers) == 1:
      continue

    entries = row.find_all("td")
    if cache_duration > 0:
      entries = cached_entries + list(entries)
      cached_entries -= 1

    if len(current_headers) != len(entries):
      print(f"skipping row, headers and entries didn't match: {row}")
      continue

    first_entry_rowspan = entries[0].get("rowspan")
    if first_entry_rowspan and is_int(first_entry_rowspan):
      rowspan = int(first_entry_rowspan)
      if rowspan > 1:
        cached_entries = [entry for entry in entries if entry.get("rowspan")]
        cache_duration = rowspan - 1

    data = {}
    for header, entry in zip(current_headers, entries):
      data[header] = entry
    
    missing_fields = [field for field in MATCH_ROW_REQUIRED_FIELDS if field not in data]
    if missing_fields:
      print(f"skipping row, missing fields {missing_fields}: {row}")
      continue

    team_a_fullname = data["team1"].get_text().strip()
    team_b_fullname = data["team2"].get_text().strip()
    team_a_shortname = data["blue"].get_text().strip()
    team_b_shortname = data["red"].get_text().strip()
    result = data["result"].get_text().strip().split("-")
    result_left = int(result[0].strip())
    result_right = int(result[1].strip())

    time_string = data["utc"].get_text().strip()

    try:
      time = datetime.strptime(time_string, MATCH_UTC_FORMAT)
    except:
      print(f"skipping row, failed to parse time string: {time_string}")
      continue
      
    rpgid = data["rpgid"].get_text().strip()
    team_a = get_or_create_team(team_a_fullname, team_a_shortname)
    team_b = get_or_create_team(team_b_fullname, team_b_shortname)
    if result_left > result_right:
      winner = team_a.id
    else:
      winner = team_b.id

    game = Game.objects.filter(rpgid=rpgid).first()
    if not game:
      game = Game(
        team_a=team_a,
        team_b=team_b,
        winner=winner,
        tournament=tournament,
        time=time,
        rpgid=rpgid,
        statistics_loaded=False
      )
      game.save()
    
    games.append(game)
  return games


