import requests
from bs4 import BeautifulSoup
import urllib.parse
from ..models import Team, Player, PlayerStat, Game, Tournament

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"

class Stat:
  def __init__(self, name, matcher):
    self.name = name
    self.matcher = matcher

  def matches(self, title):
    return title == self.matcher

STAT_MATCHERS = [
  Stat("level", "level"),
  Stat("kills", "kills"),
  Stat("deaths", "deaths"),
  Stat("assists", "assists"),
  Stat("kda", "kda"),
  Stat("cs", "cs"),
  Stat("cs_in_team_jungle", "cs in team's jungle"),
  Stat("cs_in_enemy_jungle", "cs in enemy jungle"),
  Stat("csm", "csm"),
  Stat("golds", "golds"),
  Stat("gpm", "gpm"),
  Stat("gold_share", "gold%"),
  Stat("vision_score", "vision score"),
  Stat("wards_placed", "wards placed"),
  Stat("wards_destroyed", "wards destroyed"),
  Stat("control_wards_purchased", "control wards purchased"),
  Stat("detector_wards_placed", "detector wards placed"),
  Stat("vspm", "vspm"),
  Stat("wpm", "wpm"),
  Stat("vwpm", "vwpm"),
  Stat("wcpm", "wcpm"),
  Stat("vs_share", "vs%"),
  Stat("total_damage_to_champion", "total damage to champion"),
  Stat("physical_damage", "physical damage"),
  Stat("magic_damage", "magic damage"),
  Stat("true_damage", "true damage"),
  Stat("dpm", "dpm"),
  Stat("dmg_share", "dmg%"),
  Stat("kapm", "k+a per minute"),
  Stat("kill_participation", "kp%"),
  Stat("solo_kills", "solo kills"),
  Stat("double_kills", "double kills"),
  Stat("triple_kills", "triple kills"),
  Stat("quadra_kills", "quadra kills"),
  Stat("penta_kills", "penta kills"),
  Stat("gold_diff_15", "gd@15"),
  Stat("cs_diff_15", "csd@15"),
  Stat("xp_diff_15", "xpd@15"),
  Stat("level_diff_15", "lvld@15"),
  Stat("objectives_stolen", "objectives stolen"),
  Stat("turret_damage", "damage dealt to turrets"),
  Stat("building_damage", "damage dealt to buildings"),
  Stat("heal", "total heal"),
  Stat("ally_heal", "total heals on teammates"),
  Stat("self_mitigated", "damage self mitigated"),
  Stat("total_ally_shielded", "total damage shielded on teammates"),
  Stat("cc_time_others", "time ccing others"),
  Stat("total_cc", "total time cc dealt"),
  Stat("damage_taken", "total damage taken"),
  Stat("time_dead", "total time spent dead"),
  Stat("consumables_purchased", "consumables purchased"),
  Stat("items_purchased", "items purchased"),
  Stat("shutdown_collected", "shutdown bounty collected"),
  Stat("shutdown_lost", "shutdown bounty lost")
]

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

def get_game_teams(game_id):
  teams = []
  tournament = None
  url = f"https://gol.gg/game/stats/{game_id}/page-game/"
  print(url)
  resp = requests.get(url, headers={"user-agent": user_agent})
  soup = BeautifulSoup(resp.text, "html.parser")
  for link in soup.select("a:not(.nav-link)"):
    href = link.get("href")
    if href and href.startswith("../teams"):
      parts = href.split("/")
      team_id = parts[3]
      tournament = parts[-2]
      try:
        team = Team.objects.get(team_id=team_id)
        teams.append(team)
      except:
        pass
  return (teams, tournament)

def get_game(game_id):
  teams, tournament = get_game_teams(game_id)
  if len(teams) != 2:
    raise Exception(f"didn't find 2 teams: {', '.join(str(x) for x in teams)}")

  if not tournament:
    raise Exception(f"failed to find a tournament!")
  
  tournament_name = urllib.parse.unquote(tournament.split("-", maxsplit=1)[1])
  print(tournament)

  try:
    tournament = Tournament.objects.get(name=tournament_name)
  except:
    tournament = Tournament(name=tournament_name)
    tournament.save()

  game = Game(game_id=game_id, team_a=teams[0], team_b=teams[1], tournament=tournament)
  game.save()
  return game

def get_game_and_stats(game_id):
  try:
    game = Game.objects.get(game_id=game_id)
  except:
    game = get_game(game_id)

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
          player = Player.objects.get(in_game_name__iexact=player_name)
          players.append(player)
        except:
          raise Exception(f"failed to find player with name {player_name}")

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
      try:
        Game.objects.get(game_id=game_id)
      except:
        missing_game_ids.append(game_id)
  return missing_game_ids

def update_game_data(tournament):
  for game_id in get_missing_games(tournament):
    get_game_and_stats(game_id)

def refresh_game_data(tournament):
  for game in Game.objects.filter(tournament__name=tournament):
    get_game_and_stats(game.game_id)
