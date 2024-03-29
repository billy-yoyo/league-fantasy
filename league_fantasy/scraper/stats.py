
class StatName:
  level = "level"
  kills = "kills"
  deaths = "deaths"
  assists = "assists"
  kda = "kda"
  cs = "cs"
  minions_killed = "minions_killed"
  cs_in_team_jungle = "cs_in_team_jungle"
  cs_in_enemy_jungle = "cs_in_enemy_jungle"
  golds = "golds"
  vision_score = "vision_score"
  wards_placed = "wards_placed"
  wards_destroyed = "wards_destroyed"
  detector_wards_placed = "detector_wards_placed"
  total_damage_to_champion = "total_damage_to_champion"
  dmg_share = "dmg_share"
  kill_participation = "kill_participation"
  solo_kills = "solo_kills"
  quick_solo_kills = "quick_solo_kills"
  double_kills = "double_kills"
  triple_kills = "triple_kills"
  quadra_kills = "quadra_kills"
  penta_kills = "penta_kills"
  gold_diff_15 = "gold_diff_15"
  cs_diff_15 = "cs_diff_15"
  xp_diff_15 = "xp_diff_15"
  level_diff_15 = "level_diff_15"
  objectives_stolen = "objectives_stolen"
  turret_damage = "turret_damage"
  building_damage = "building_damage"
  objective_damage = "objective_damage"
  heal = "heal"
  ally_heal = "ally_heal"
  self_mitigated = "self_mitigated"
  total_ally_shielded = "total_ally_shielded"
  cc_time_others = "cc_time_others"
  total_cc = "total_cc"
  damage_taken = "damage_taken"
  time_dead = "time_dead"
  consumables_purchased = "consumables_purchased"
  items_purchased = "items_purchased"
  shutdown_collected = "shutdown_collected"
  shutdown_lost = "shutdown_lost"
  cs_neutral_minions = "cs_neutral_minions"
  alcove_kills = "alcove_kills"
  turret_plates = "turret_plates"

def create_stat_matcher(matcher_string):
  parts = matcher_string.split(".")
  def matcher(obj):
    result = obj
    for part in parts:
      if result:
        result = result.get(part, None)
    return result
  return matcher

class Stat:
  def __init__(self, name, matcher):
    self.name = name
    self.matcher = create_stat_matcher(matcher)

  def get_value(self, obj):
    return self.matcher(obj) or 0

# The following stats are found via the timeline:
#   gold_diff_15
#   cs_diff_15
#   xp_diff_15
#   level_diff_15
#   shutdown_collected
#   shutdown_lost
#   cs

STAT_MATCHERS = [
  Stat(StatName.level, "champLevel"),
  Stat(StatName.kills, "kills"),
  Stat(StatName.deaths, "deaths"),
  Stat(StatName.assists, "assists"),
  Stat(StatName.kda, "challenges.kda"),
  Stat(StatName.minions_killed, "totalMinionsKilled"),
  Stat(StatName.cs_in_team_jungle, "totalAllyJungleMinionsKilled"),
  Stat(StatName.cs_in_enemy_jungle, "totalEnemyJungleMinionsKilled"),
  Stat(StatName.cs_neutral_minions, "neutralMinionsKilled"),
  Stat(StatName.golds, "goldEarned"),
  Stat(StatName.vision_score, "visionScore"),
  Stat(StatName.wards_placed, "wardsPlaced"),
  Stat(StatName.wards_destroyed, "wardsKilled"),
  Stat(StatName.detector_wards_placed, "detectorWardsPlaced"),
  Stat(StatName.total_damage_to_champion, "totalDamageDealtToChampions"),
  Stat(StatName.dmg_share, "challenges.teamDamagePercentage"),
  Stat(StatName.kill_participation, "challenges.killParticipation"),
  Stat(StatName.solo_kills, "challenges.soloKills"),
  Stat(StatName.quick_solo_kills, "challenges.quickSoloKills"),
  Stat(StatName.double_kills, "doubleKills"),
  Stat(StatName.triple_kills, "tripleKills"),
  Stat(StatName.quadra_kills, "quadraKills"),
  Stat(StatName.penta_kills, "pentaKills"),
  Stat(StatName.objectives_stolen, "objectivesStolen"),
  Stat(StatName.turret_damage, "damageDealtToTurrets"),
  Stat(StatName.building_damage, "damageDealtToBuildings"),
  Stat(StatName.objective_damage, "damageDealtToObjectives"),
  Stat(StatName.heal, "totalHeal"),
  Stat(StatName.ally_heal, "totalHealsOnTeammates"),
  Stat(StatName.self_mitigated, "damageSelfMitigated"),
  Stat(StatName.total_ally_shielded, "totalDamageShieldedOnTeammates"),
  Stat(StatName.cc_time_others, "timeCCingOthers"),
  Stat(StatName.total_cc, "totalTimeCCDealt"),
  Stat(StatName.damage_taken, "totalDamageTaken"),
  Stat(StatName.time_dead, "totalTimeSpentDead"),
  Stat(StatName.consumables_purchased, "consumablesPurchased"),
  Stat(StatName.items_purchased, "itemsPurchased"),
  Stat(StatName.alcove_kills, "challenges.takedownsInAlcove"),
  Stat(StatName.turret_plates, "challenges.turretPlatesTaken")
]
