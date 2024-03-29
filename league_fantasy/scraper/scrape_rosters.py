import requests
from bs4 import BeautifulSoup
from ..models import Player, Team
from .stats import STAT_MATCHERS

def get_or_create_player(team, in_game_name, position):
  player = Player.objects.filter(in_game_name__iexact=in_game_name).first()
  if not player:
    player = Player(
      team=team,
      in_game_name=in_game_name,
      position=position,
      active=True
    )
    player.save()
  else:
    player.active = True
    player.save()
  return player

ROLE_TITLE_TO_POSITION = {
  "top laner": "top",
  "jungler": "jungle",
  "mid laner": "mid",
  "bot laner": "bot",
  "support": "support"
}

def scrape_rosters(tournament):
  # set all current teams + players as inactive
  Team.objects.update(active=False)
  Player.objects.update(active=False)

  tournament_name = tournament.name
  season_name = tournament.season.name

  resp = requests.get(f"https://lol.fandom.com/wiki/LEC/{season_name}/{tournament_name}/Team_Rosters")
  soup = BeautifulSoup(resp.text, "lxml")

  current_team = None
  for node in soup.select("h3 .teamname, table.extended-rosters tbody tr"):
    if node.name == "span":
      team_name = node.get_text().strip()
      current_team = Team.objects.filter(full_name__iexact=team_name).first()
      current_team.active = True
      current_team.save()
    elif current_team:
      role_sprite = node.select_one(".role-sprite")
      if not role_sprite:
        continue
      role_title = role_sprite.get("title")
      if not role_title:
        continue
      role_title = role_title.strip().lower()
      if role_title not in ROLE_TITLE_TO_POSITION:
        continue

      position = ROLE_TITLE_TO_POSITION[role_title]
      player_link = node.select_one(".extended-rosters-id")
      if not player_link:
        print(f"no link for player in position {player_link}")
        continue
      player_name = player_link.get_text().strip()

      get_or_create_player(current_team, player_name, position)


