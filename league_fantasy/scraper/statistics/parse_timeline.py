from ...models import PlayerStat
from .stats import StatName
from .teamfight_detector import find_teamfights
from collections import defaultdict

FIFTEEN_MINUTES = 15 * 60 * 1000

def find_frame_for_time(frames, millis):
  closest_frame = None
  closest_frame_gap = None
  for frame in frames:
    gap = abs(frame["timestamp"] - millis)
    if closest_frame_gap is None or gap < closest_frame_gap:
      closest_frame_gap = gap
      closest_frame = frame
  return closest_frame

def calculate_15_min_differences(timeline, game, players, participant_map):
  min15_frame = find_frame_for_time(timeline["frames"], FIFTEEN_MINUTES)
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
  
  return player_stats

def calculate_bounties(timeline, game, players, participant_map):
  player_stats = []
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

  return player_stats

def calculate_final_frame(timeline, game, players, participant_map):
  player_stats = []
  last_frame = timeline["frames"][-1]
  
  for player in players:
    pid = participant_map[player.id]
    pframe = last_frame["participantFrames"][str(pid)]
    final_cs = pframe["jungleMinionsKilled"] + pframe["minionsKilled"]
    player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.cs, stat_value=final_cs))

  return player_stats

def compute_ganks(team_participants, enemy_participants, pid_to_player, pre15_ganks):
  jungler = [pid_to_player[pid] for pid in team_participants if pid_to_player[pid].position == "jungle"]
  support = [pid_to_player[pid] for pid in team_participants if pid_to_player[pid].position == "support"]
  mid = [pid_to_player[pid] for pid in team_participants if pid_to_player[pid].position == "mid"]
  top = [pid_to_player[pid] for pid in team_participants if pid_to_player[pid].position == "top"]
  if len(jungler) > 0:
    for player in jungler:
      pre15_ganks[player.id] += 1
  # it only counts as a support gank if the adc isn't in the fight
  elif len(support) > 0 and all(pid_to_player[pid].position != "bot" for pid in team_participants):
    for player in support:
      pre15_ganks[player.id] += 1
  elif len(mid) > 0 and all(pid_to_player[pid].position != "mid" for pid in enemy_participants):
    for player in mid:
      pre15_ganks[player.id] += 1
  elif len(top) > 0 and all(pid_to_player[pid].position != "top" for pid in enemy_participants):
    for player in top:
      pre15_ganks[player.id] += 1

def calculate_teamfights(data, timeline, game, players, participant_map):
  teamfights = find_teamfights(timeline)
  team_pids = defaultdict(list)
  pid_to_team = {
    p["participantId"]: p["teamId"] for p in data["participants"]
  }
  pid_to_player = {}

  for player in players:
    pid = participant_map[player.id]
    team_id = pid_to_team[pid]
    team_pids[team_id].append(pid)
    pid_to_player[pid] = player
  
  if len(team_pids) != 2:
    print(f"not exactly 2 teams??")
    return []

  solo_death_in_teamfight = defaultdict(int)
  pre15_ganks = defaultdict(int)

  for teamfight in teamfights:
    team_deaths = [[pid for pid in pids if pid in teamfight.deaths] for pids in team_pids.values()]
    team_participants = [[pid for pid in pids if pid in teamfight.participants] for pids in team_pids.values()]

    if teamfight.start <= FIFTEEN_MINUTES:
      # a successful(ish) gank
      if len(team_deaths[0]) <= len(team_deaths[1]):
        compute_ganks(team_participants[0], team_participants[1], pid_to_player, pre15_ganks)
      if len(team_deaths[1]) <= len(team_deaths[0]):
        compute_ganks(team_participants[1], team_participants[0], pid_to_player, pre15_ganks)

    # no winner
    if len(team_deaths[0]) == len(team_deaths[1]):
      continue

    winner = min(team_deaths, key=lambda x: len(x))
    loser = max(team_deaths, key=lambda x: len(x))

    # one person died in a teamfight, we record this stat
    if len(winner) == 1:
      solo_death_in_teamfight[pid_to_player[winner[0]].id] += 1

  player_stats = []
  for player in players:
    player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.only_death_in_teamfight_win, stat_value=solo_death_in_teamfight[player.id]))
    player_stats.append(PlayerStat(player=player, game=game, stat_name=StatName.ganks_15, stat_value=pre15_ganks[player.id]))

  return player_stats

def scrape_match_timeline(data, timeline, game, players, participant_map):
  player_stats = []
  
  player_stats += calculate_15_min_differences(timeline, game, players, participant_map)
  player_stats += calculate_bounties(timeline, game, players, participant_map)
  player_stats += calculate_final_frame(timeline, game, players, participant_map)
  player_stats += calculate_teamfights(data, timeline, game, players, participant_map)

  return player_stats
