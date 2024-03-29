from ..models import Game, Player, PlayerStat, Team, GamePlayer
from .stats import STAT_MATCHERS, StatName
from collections import defaultdict
from .esclient import esclient
import json

def find_frame_for_time(frames, millis):
  closest_frame = None
  closest_frame_gap = None
  for frame in frames:
    gap = abs(frame["timestamp"] - millis)
    if closest_frame_gap is None or gap < closest_frame_gap:
      closest_frame_gap = gap
      closest_frame = frame
  return closest_frame

def scrape_match_timeline(timeline, game, players, participant_map):
  min15_frame = find_frame_for_time(timeline["frames"], 15 * 60 * 1000)
  last_frame = timeline["frames"][-1]
  position_players_map = defaultdict(list)
  for player in players:
    position_players_map[player.position].append(player)
  
  player_stats = []
  # calculate @15 difference stats
  for position_players in position_players_map.values():
    if len(position_players) != 2:
      continue

    player1, player2 = position_players
    pid1 = participant_map[player1.id]
    pid2 = participant_map[player2.id]

    p1frame = min15_frame["participantFrames"][str(pid1)]
    p2frame = min15_frame["participantFrames"][str(pid2)]

    p1gold = p1frame["totalGold"]
    p1level = p1frame["level"]
    p1xp = p1frame["xp"]
    p1cs = p1frame["minionsKilled"] + p1frame["jungleMinionsKilled"]

    p2gold = p2frame["totalGold"]
    p2level = p2frame["level"]
    p2xp = p2frame["xp"]
    p2cs = p2frame["minionsKilled"] + p2frame["jungleMinionsKilled"]

    gold_diff = p1gold - p2gold
    level_diff = p1level - p2level
    xp_diff = p1xp - p2xp
    cs_diff = p1cs - p2cs

    player_stats.append(PlayerStat(player=player1, game=game, stat_name=StatName.gold_diff_15, stat_value=gold_diff))
    player_stats.append(PlayerStat(player=player1, game=game, stat_name=StatName.level_diff_15, stat_value=level_diff))
    player_stats.append(PlayerStat(player=player1, game=game, stat_name=StatName.xp_diff_15, stat_value=xp_diff))
    player_stats.append(PlayerStat(player=player1, game=game, stat_name=StatName.cs_diff_15, stat_value=cs_diff))

    player_stats.append(PlayerStat(player=player2, game=game, stat_name=StatName.gold_diff_15, stat_value=-gold_diff))
    player_stats.append(PlayerStat(player=player2, game=game, stat_name=StatName.level_diff_15, stat_value=-level_diff))
    player_stats.append(PlayerStat(player=player2, game=game, stat_name=StatName.xp_diff_15, stat_value=-xp_diff))
    player_stats.append(PlayerStat(player=player2, game=game, stat_name=StatName.cs_diff_15, stat_value=-cs_diff))

  bounties_given = defaultdict(int)
  bounties_taken = defaultdict(int)

  # calculate bounty stats
  for frame in timeline["frames"]:
    for event in frame["events"]:
      if event.get("type", "") != "CHAMPION_KILL":
        continue

      killer = event["killerId"]
      victim = event["victimId"]
      bounty = event["shutdownBounty"]

      if bounty > 0:
        bounties_taken[int(killer)] += bounty
        bounties_given[int(victim)] += bounty
  
  for player in players:
    pid = participant_map[player.id]
    player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.shutdown_collected, stat_value=bounties_taken[pid]))
    player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.shutdown_lost, stat_value=bounties_given[pid]))

    pframe = last_frame["participantFrames"][str(pid)]
    final_cs = pframe["jungleMinionsKilled"] + pframe["minionsKilled"]
    player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.cs, stat_value=final_cs))

  return player_stats

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
  
  all_player_stats += scrape_match_timeline(timeline, game, players, participant_map)

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

