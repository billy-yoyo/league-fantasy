from .stats import StatName
from ..score_computer import ScoreComputer
import math

def calculate_lane_performance(position, duration, stats, score):
  solo_kills = stats.get(StatName.solo_kills)
  pick_with_ally = stats.get(StatName.pick_with_ally)
  gd15 = stats.get(StatName.gold_diff_15)
  xpd15 = stats.get(StatName.xp_diff_15)
  cspm = stats.get(StatName.cs) / duration
  first_blood = stats.get(StatName.first_blood)

  score.add("solo kill", solo_kills)

  if position == "mid":
    score.add("pick with ally", math.floor(pick_with_ally / 3))
  else:
    score.add("pick with ally", math.floor(pick_with_ally / 5))

  if gd15 > 1000:
    score.add("gd15", 3)
  elif gd15 > 0:
    score.add("gd15", 1)
  
  if xpd15 > 1000:
    score.add("xpd15", 3)
  elif xpd15 > 0:
    score.add("xpd15", 1)
  
  if cspm >= 8:
    score.add("cspm", math.floor(cspm - 8))

  score.add("first blood", first_blood * 2)


def calculate_objectives(duration, stats, score):
  vision_score_pm = stats.get(StatName.vision_score) / duration
  turret_damage = stats.get(StatName.turret_damage)
  turret_plates = stats.get(StatName.turret_plates)
  control_ward_pct = stats.get(StatName.control_ward_pct)
  objectives_secured = stats.get(StatName.epic_monster_secured)
  objectives_stolen = stats.get(StatName.objectives_stolen)

  score.add("vision", math.floor(vision_score_pm))
  
  if turret_damage > 5000:
    score.add("turret", math.floor((turret_damage - 5000) // 1000))

  score.add("turret plates", turret_plates)

  if control_ward_pct > 0.6:
    score.add("control ward %", math.floor((control_ward_pct * 10) - 6))
  
  score.add("objectives secured", objectives_secured * 2)
  score.add("objectives stolen", objectives_stolen * 3)


def calculate_teamfights(position, duration, stats, score):
  damage_taken_pm = stats.get(StatName.damage_taken) / duration
  self_mitigated_pm = stats.get(StatName.self_mitigated) / duration
  heal_shield_pm = (stats.get(StatName.ally_heal) + stats.get(StatName.total_ally_shielded)) / duration
  dpm = stats.get(StatName.total_damage_to_champion) / duration
  immobilisations = stats.get(StatName.immobilisations)
  immobilise_and_kill = stats.get(StatName.immobilise_and_kill)
  knock_into_team_and_kill = stats.get(StatName.knock_into_team_and_kill)

  score.add("damage taken", math.floor(damage_taken_pm / 666))
  score.add("self mitigated", math.floor(self_mitigated_pm / 666))
  score.add("heals and shields", math.floor(heal_shield_pm / 50))
  score.add("knock into team & kill", math.floor(knock_into_team_and_kill / 3))
  score.add("immobilize & kill", math.floor(immobilise_and_kill / 5))
  
  if position != "support":
    if dpm >= 600:
      dpm_value = math.floor(dpm // 100) - 5
      if position == "mid":
        score.add("dpm", dpm_value * 2)
      else:
        score.add("dpm", dpm_value)
    elif dpm < 200:
      score.add("dpm", -1)

  score.add("immobilisations", math.floor(immobilisations / 20))


def calculate_scoreline(position, stats, score):
  kda = stats.get(StatName.kda)
  deaths = stats.get(StatName.deaths)

  if position == "support":
    if deaths == 0 or kda >= 10:
      score.add("kda", 1)
    else:
      score.add("kda", 0)
  elif deaths == 0:
    score.add("kda", 8)
  elif kda >= 10:
    score.add("kda", 5)
  elif kda >= 5:
    score.add("kda", 2)
  elif kda >= 1:
    score.add("kda", 1)
  else:
    score.add("kda", -2)
  


def calculate_multikill_score(stats):
  doubles = stats.get(StatName.double_kills, 0)
  triples = stats.get(StatName.triple_kills, 0)
  quadras = stats.get(StatName.quadra_kills, 0)
  pentas = stats.get(StatName.penta_kills, 0)

  # we don't want to double-count
  doubles -= pentas
  triples -= pentas
  quadras -= pentas

  doubles -= quadras
  triples -= quadras

  doubles -= triples

  return doubles + (triples * 2) + (quadras * 3) + (pentas * 5)


def calculate_montage(stats, score):
  alcove_kills = stats.get(StatName.alcove_kills)
  heavy_damage_survive = stats.get(StatName.take_heavy_damage_survive)

  calculate_multikill_score(stats)

  score.add("alcove kills", alcove_kills)
  score.add("heavy damage & survive", heavy_damage_survive * 2)


def calculate_jungle(stats, score):
  baron_kill = stats.get(StatName.baron_kill)
  early_dragon = stats.get(StatName.early_dragon)
  kp = stats.get(StatName.kill_participation)
  takedown_all_lanes = stats.get(StatName.takedown_all_lanes_early)

  score.add("barons", baron_kill)

  if early_dragon > 0:
    score.add("early dragon", max(math.floor((480 - early_dragon) / 60), 0))

  score.add("takedown all lanes early", takedown_all_lanes * 2)

  if kp >= 0.9:
    score.add("kp", 2)
  elif kp < 0.3:
    score.add("kp", -2)


def calculate_support(stats, score):
  save_ally = stats.get(StatName.save_ally)
  only_death_in_teamfight_win = stats.get(StatName.only_death_in_teamfight_win)
  kp = stats.get(StatName.kill_participation)

  score.add("save ally", save_ally)
  score.add("only death in teamfight win", only_death_in_teamfight_win)
  
  if kp >= 0.9:
    score.add("kp", 2)
  elif kp < 0.3:
    score.add("kp", -2)


def calculate_score(game, position, stats):
  duration = game.game_duration
  score = ScoreComputer(0)

  score.add("games", -10)

  calculate_lane_performance(position, duration, stats, score)
  calculate_objectives(duration, stats, score)
  calculate_teamfights(position, duration, stats, score)
  calculate_scoreline(position, stats, score)
  calculate_montage(stats, score)

  if position == "jungle":
    calculate_jungle(stats, score)
  elif position == "support":
    calculate_support(stats, score)

  return score