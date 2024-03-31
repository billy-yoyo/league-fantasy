import math

TEAMFIGHT_MAX_INTERVAL = 30_000 # 30 seconds
TEAMFIGHT_MAX_DISTANCE = 100

def format_timestamp(timestamp):
  total_seconds = timestamp // 1000
  minutes = total_seconds // 60
  minute_seconds = total_seconds % 60
  return f"{minutes}:{minute_seconds}" 

class Teamfight:
  def __init__(self, kills, start, end, participants, positions, deaths):
    self.kills = kills
    self.start = start
    self.end = end
    self.participants = participants
    self.positions = positions
    self.deaths = deaths

  def __str__(self) -> str:
    return f"Teamfight from {format_timestamp(self.start)} to {format_timestamp(self.end)}"

def distance(p1, p2):
  dx = p1["x"] - p2["x"]
  dy = p1["y"] - p2["y"]
  return math.sqrt((dx * dx) + (dy * dy))

def minimum_distance(position, other_positions):
  return min(distance(position, other_position) for other_position in other_positions)

def distance_within_range(position, other_positions, max_dist):
  return minimum_distance(position, other_positions) <= max_dist

def find_teamfights(timeline):
  kills = {}
  kill_ids = []
  kill_index = 0

  # this should be sorted chronologically already
  for frame in timeline["frames"]:
    for event in frame["events"]:
      if event["type"] == "CHAMPION_KILL":
        kill_index += 1
        kill_ids.append(kill_index)
        kills[kill_index] = event
    
  teamfights = []
  visited = []
  for i, kill_id in enumerate(kill_ids):
    if kill_id in visited:
      continue
    
    last_kill = kills[kill_id]
    teamfight = [kill_id]
    teamfight_positions = [last_kill["position"]]
    teamfight_participants = set(last_kill.get("assistingParticipantIds", []) + [last_kill["killerId"], last_kill["victimId"]])
    teamfight_deaths = {last_kill["victimId"]}

    j = i + 1
    while j < len(kill_ids):
      next_kill_id = kill_ids[j]
      j += 1

      if next_kill_id in visited:
        continue
      next_kill = kills[next_kill_id]

      # is this kill too far in the futuer?
      elapsed = next_kill["timestamp"] - last_kill["timestamp"]
      if elapsed > TEAMFIGHT_MAX_INTERVAL:
        # this teamfight has finished, the next kill is too far in the future to consider
        break

      participants = set(last_kill.get("assistingParticipantIds", []) + [last_kill["killerId"], last_kill["victimId"]])

      has_participan_overlap = len(participants & teamfight_participants) > 0
      same_teamfight = has_participan_overlap or distance_within_range(next_kill["position"], teamfight_positions, TEAMFIGHT_MAX_DISTANCE)

      if same_teamfight:
        teamfight_participants |= participants
        teamfight_positions.append(next_kill["position"])
        teamfight.append(next_kill_id)
        teamfight_deaths.add(next_kill["victimId"])
        visited.append(next_kill_id)

    teamfight_start = min(kills[kid]["timestamp"] for kid in teamfight)
    teamfight_end = max(kills[kid]["timestamp"] for kid in teamfight)
    teamfights.append(Teamfight(teamfight, teamfight_start, teamfight_end, teamfight_participants, teamfight_positions, list(teamfight_deaths)))

  return teamfights
