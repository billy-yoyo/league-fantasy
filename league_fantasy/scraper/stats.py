
class StatName:
  level = "level"
  kills = "kills"
  deaths = "deaths"
  assists = "assists"
  kda = "kda"
  cs = "cs"
  cs_in_team_jungle = "cs_in_team_jungle"
  cs_in_enemy_jungle = "cs_in_enemy_jungle"
  csm = "csm"
  golds = "golds"
  gpm = "gpm"
  gold_share = "gold_share"
  vision_score = "vision_score"
  wards_placed = "wards_placed"
  wards_destroyed = "wards_destroyed"
  control_wards_purchased = "control_wards_purchased"
  detector_wards_placed = "detector_wards_placed"
  vspm = "vspm"
  wpm = "wpm"
  vwpm = "vwpm"
  wcpm = "wcpm"
  vs_share = "vs_share"
  total_damage_to_champion = "total_damage_to_champion"
  physical_damage = "physical_damage"
  magic_damage = "magic_damage"
  true_damage = "true_damage"
  dpm = "dpm"
  dmg_share = "dmg_share"
  kapm = "kapm"
  kill_participation = "kill_participation"
  solo_kills = "solo_kills"
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

class Stat:
  def __init__(self, name, matcher):
    self.name = name
    self.matcher = matcher

  def matches(self, title):
    return title == self.matcher

STAT_MATCHERS = [
  Stat(StatName.level, "level"),
  Stat(StatName.kills, "kills"),
  Stat(StatName.deaths, "deaths"),
  Stat(StatName.assists, "assists"),
  Stat(StatName.kda, "kda"),
  Stat(StatName.cs, "cs"),
  Stat(StatName.cs_in_team_jungle, "cs in team's jungle"),
  Stat(StatName.cs_in_enemy_jungle, "cs in enemy jungle"),
  Stat(StatName.csm, "csm"),
  Stat(StatName.golds, "golds"),
  Stat(StatName.gpm, "gpm"),
  Stat(StatName.gold_share, "gold%"),
  Stat(StatName.vision_score, "vision score"),
  Stat(StatName.wards_placed, "wards placed"),
  Stat(StatName.wards_destroyed, "wards destroyed"),
  Stat(StatName.control_wards_purchased, "control wards purchased"),
  Stat(StatName.detector_wards_placed, "detector wards placed"),
  Stat(StatName.vspm, "vspm"),
  Stat(StatName.wpm, "wpm"),
  Stat(StatName.vwpm, "vwpm"),
  Stat(StatName.wcpm, "wcpm"),
  Stat(StatName.vs_share, "vs%"),
  Stat(StatName.total_damage_to_champion, "total damage to champion"),
  Stat(StatName.physical_damage, "physical damage"),
  Stat(StatName.magic_damage, "magic damage"),
  Stat(StatName.true_damage, "true damage"),
  Stat(StatName.dpm, "dpm"),
  Stat(StatName.dmg_share, "dmg%"),
  Stat(StatName.kapm, "k+a per minute"),
  Stat(StatName.kill_participation, "kp%"),
  Stat(StatName.solo_kills, "solo kills"),
  Stat(StatName.double_kills, "double kills"),
  Stat(StatName.triple_kills, "triple kills"),
  Stat(StatName.quadra_kills, "quadra kills"),
  Stat(StatName.penta_kills, "penta kills"),
  Stat(StatName.gold_diff_15, "gd@15"),
  Stat(StatName.cs_diff_15, "csd@15"),
  Stat(StatName.xp_diff_15, "xpd@15"),
  Stat(StatName.level_diff_15, "lvld@15"),
  Stat(StatName.objectives_stolen, "objectives stolen"),
  Stat(StatName.turret_damage, "damage dealt to turrets"),
  Stat(StatName.building_damage, "damage dealt to buildings"),
  Stat(StatName.heal, "total heal"),
  Stat(StatName.ally_heal, "total heals on teammates"),
  Stat(StatName.self_mitigated, "damage self mitigated"),
  Stat(StatName.total_ally_shielded, "total damage shielded on teammates"),
  Stat(StatName.cc_time_others, "time ccing others"),
  Stat(StatName.total_cc, "total time cc dealt"),
  Stat(StatName.damage_taken, "total damage taken"),
  Stat(StatName.time_dead, "total time spent dead"),
  Stat(StatName.consumables_purchased, "consumables purchased"),
  Stat(StatName.items_purchased, "items purchased"),
  Stat(StatName.shutdown_collected, "shutdown bounty collected"),
  Stat(StatName.shutdown_lost, "shutdown bounty lost")
]
