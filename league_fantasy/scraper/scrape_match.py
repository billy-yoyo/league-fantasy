from ..models import Game, Player, PlayerStat, Team, GamePlayer
from .statistics.stats import STAT_MATCHERS, StatName
from .statistics.parse_timeline import scrape_match_timeline
from collections import defaultdict
from .esclient import esclient
import json



def parse_participant(game, data):
  # parse player 
  in_game_name_with_tag = data["riotIdGameName"].strip().split(" ", 1)
  team_tag, in_game_name = in_game_name_with_tag

  player = Player.objects.filter(in_game_name__iexact=in_game_name).first()
  if not player:
    print(f"failed to find player with in game name {in_game_name}")
    return None, None, [], None
  
  player_stats = []
  for stat in STAT_MATCHERS:
    value = stat.get_value(data)
    player_stats.append(PlayerStat(player=player, game=game, stat_name=stat.name, stat_value=value))

  first_blood = int(data["firstBloodKill"] or data["firstBloodAssist"])
  player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.first_blood, stat_value=first_blood))

  team = Team.objects.filter(short_name__iexact=team_tag).first()
  if not team:
    print(f"failed to find team with tag {team_tag}")
    return None, None, [], None
  
  # we assume that at the time of loading this game, the current position of the player in the database is 
  # also the position they played in this game. This isn't necessarily true, but it's impossible to figure out
  # from the game data alone what role a person played in an individual game. This will mean fetching historical
  # data will be buggy, but this should be a good solution for on-going data collection.
  game_player = GamePlayer(game=game, player=player, team=team, position=player.position)

  return data["participantId"], player, player_stats, game_player

def scrape_match(game):
  data, timeline = esclient.get_data_and_timeline(game.rpgid, version=5)
  participant_map = {}
  players = []
  all_player_stats = []
  all_game_players = []
  for participant_data in data["participants"]:
    participant_id, player, player_stats, game_player = parse_participant(game, participant_data)
    all_player_stats += player_stats
    if player:
      players.append(player)
      participant_map[player.id] = participant_id
      all_game_players.append(game_player)
  
  all_player_stats += scrape_match_timeline(data, timeline, game, players, participant_map)

  # we don't want duplicate stats and players when refreshing!
  PlayerStat.objects.filter(game=game).delete()
  GamePlayer.objects.filter(game=game).delete()

  PlayerStat.objects.bulk_create(all_player_stats)
  GamePlayer.objects.bulk_create(all_game_players)

  game.statistics_loaded = True
  game.game_duration = data["gameDuration"] / 60 # game duration in minutes
  game.save()
  print(f"Loaded game {game.rpgid}")


def scrape_unloaded_games(tournament):
  for game in Game.objects.filter(tournament=tournament, statistics_loaded=False):
    scrape_match(game)

def scrape_all_games(tournament):
  for game in Game.objects.filter(tournament=tournament):
    scrape_match(game)

