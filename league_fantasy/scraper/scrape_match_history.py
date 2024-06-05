from datetime import datetime
from ..models import Team, Game, Player, PlayerTournamentScore
from .esclient import esclient
from .countries import get_country_code

MATCH_UTC_FORMAT = "%Y-%m-%d %H:%M:%S"

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

def get_or_create_team(full_name, short_name, region):
  team = Team.objects.filter(full_name__iexact=full_name).first()
  if not team:
    team = Team(full_name=full_name, short_name=short_name, region=region)
    team.save()
  else:
    team.short_name = short_name
    team.region = region
    team.save()
  return team

def get_or_create_player(tournament, team, in_game_name, position, country, overview_page):
  player = Player.objects.filter(in_game_name__iexact=in_game_name).first()
  if not player:
    player = Player(
      team=team,
      in_game_name=in_game_name,
      country=country,
      position=position,
      overview_page=overview_page,
      active=True
    )
    player.save()
  else:
    player.active = True
    player.country = country
    player.position = position
    player.team = team
    player.overview_page = overview_page
    player.save()

  tournament_player = PlayerTournamentScore.objects.filter(player=player, tournament=tournament).first()
  if not tournament_player:
    PlayerTournamentScore(player=player, tournament=tournament, score=0).save()
  return player

POSITIONS = ["top", "jungle", "mid", "bot", "support"]

ROSTER_OVERRIDES = {
  "fnc": (
    "Oscarinin;;Razork;;Humanoid;;Noah (Oh Hyeon-taek);;Jun (Yoon Se-jun);;Nightshare;;Gaax",
    "Top;;Jungle;;Mid;;Bot;;Support;;Coach;;Coach"
  ),

  "g2": (
    "BrokenBlade;;Yike;;Caps;;Hans Sama;;Mikyx;;Dylan Falco;;Rodrigo",
    "Top;;Jungle;;Mid;;Bot;;Support;;Coach;;Coach"
  ),

  "mdk": (
    "Myrwn;;Elyoya;;Fresskowy;;Supa;;Alvaro (Álvaro Fernández);;Melzhet;;Zeph",
    "Top;;Jungle;;Mid;;Bot;;Support;;Coach;;Coach"
  ),

  "bds": (
    "Adam (Adam Maanane);;Sheo;;nuc;;Ice (Yoon Sang-hoon);;Labrov;;Striker (Yanis Kella);;MenQ",
    "Top;;Jungle;;Mid;;Bot;;Support;;Coach;;Coach"
  ),

  "th": (
    "Wunder;;Jankos;;Zwyroo;;Flakked;;Trymbi;;Peter Dun;;Kirei",
    "Top;;Jungle;;Mid;;Bot;;Support;;Coach;;Coach"
  )
}

def get_team_player_and_positions(short_name, team_data):
  if short_name.lower() in ROSTER_OVERRIDES:
    roster, roles = ROSTER_OVERRIDES[short_name.lower()]
  else:
    roster = team_data["RosterLinks"]
    roles = team_data["Roles"]
  roster = roster.split(";;")
  roles = roles.split(";;")
  if len(roster) != len(roles):
    print(f"Invalid roster for team {team_data['Short']}")
  
  player_positions = []
  for player, role_string in zip(roster, roles):
    position = role_string.split(",")[0].lower()
    if position not in POSITIONS:
      continue
    player_positions.append((player, position))
  return player_positions



def scrape_match_list(tournament):
  tournament_name = tournament.disambig_name

  games = []

  print("getting match history...")
  data = esclient.get_match_history(tournament_name)
  
  cached_teams = {}

  team_data_results = esclient.get_team_data(tournament_name, [])
  roster_data = {}

  for team_data in team_data_results:
    team_shortname = team_data["Short"]
    team_fullname = team_data["Name"]
    team_region = team_data["Region"]
    team_roster = get_team_player_and_positions(team_shortname, team_data)

    team = get_or_create_team(team_fullname, team_shortname, team_region)
    for player, position in team_roster:
      roster_data[player.lower()] = (team, position)
    
    cached_teams[team_data["OverviewPage"]] = team

  player_data_results = esclient.get_player_data(roster_data.keys())
  for player_data in player_data_results:
    official_name = player_data["Player"]
    in_game_name = player_data["ID"]
    overview_page = player_data["OverviewPage"] or ""
    country = get_country_code(player_data["Country"])
    if country == "NONE":
      country = get_country_code(player_data["NationalityPrimary"])
    if country == "NONE":
      print(f"player {in_game_name} has no country code: {player_data['Country']}")
    team, position = roster_data[official_name.lower()]
    get_or_create_player(tournament, team, in_game_name, position, country, overview_page)

  for match in data:
    team_a = cached_teams[match["Team1"]]
    team_b = cached_teams[match["Team2"]]

    winner_index = int(match["Winner"])

    time_string = match["DateTime UTC"]

    try:
      time = datetime.strptime(time_string, MATCH_UTC_FORMAT)
    except:
      print(f"skipping row, failed to parse time string: {time_string}")
      continue
      
    rpgid = match["RiotPlatformGameId"]
    if not rpgid:
      print(f"skipping match {match}")
      continue

    if winner_index == 1:
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
    else:
      game.team_a = team_a
      game.team_b = team_b
      game.winner = winner
      game.tournament = tournament
      game.time = time
      game.rpgid  = rpgid
      game.save
    
    games.append(game)
  return games


