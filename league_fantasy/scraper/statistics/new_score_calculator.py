from .stats import StatName, StatSource
from ..score_computer import ScoreComputer
import math

def calculate_lane_performance(position, duration, stats, score):
  solo_kills = stats.get(StatName.solo_kills)
  pick_with_ally = stats.get(StatName.pick_with_ally)

  solo_gd15 = stats.get(StatName.gold_diff_15)
  duo_gd15 = stats.get(StatName.duo_gold_diff_15)
  gd15 = duo_gd15 if position in ("bot", "support") else solo_gd15

  xpd15 = stats.get(StatName.xp_diff_15)
  cspm = stats.get(StatName.cs) / duration
  first_blood = stats.get(StatName.first_blood)
  takedown_all_lanes = stats.get(StatName.takedown_all_lanes_early)
  ganks15 = stats.get(StatName.ganks_15)

  score.add(StatSource.solo_kill, solo_kills * 3)

  if takedown_all_lanes > 0:
    score.add(StatSource.takedown_all_lanes_early, takedown_all_lanes * 2)

  if position == "mid" or position == "top":
    score.add(StatSource.pick_with_ally, math.floor(pick_with_ally / 3))
  else:
    score.add(StatSource.pick_with_ally, math.floor(pick_with_ally / 5))
  
  if gd15 >= 600:
    score.add(StatSource.gd15, math.floor((gd15 - 400) / 200))
  elif gd15 > 0:
    score.add(StatSource.gd15, 1)
  
  if xpd15 >= 600:
    score.add(StatSource.xpd15, math.floor((xpd15 - 400) / 200))
  elif xpd15 > 0:
    score.add(StatSource.xpd15, 1)

  if ganks15 > 0:
    score.add(StatSource.ganks, ganks15)
  
  if cspm >= 8:
    score.add(StatSource.cspm, math.floor(cspm - 8))

  score.add(StatSource.first_blood, first_blood * 2)


def calculate_objectives(duration, stats, score):
  vision_score_pm = stats.get(StatName.vision_score) / duration
  turret_damage = stats.get(StatName.turret_damage)
  turret_plates = stats.get(StatName.turret_plates)
  control_ward_pct = stats.get(StatName.control_ward_pct)
  objectives_secured = stats.get(StatName.epic_monster_secured)
  objectives_stolen = stats.get(StatName.objectives_stolen)

  score.add(StatSource.vision, math.floor(vision_score_pm))
  
  if turret_damage > 5000:
    score.add(StatSource.turret, math.floor((turret_damage - 5000) // 1000))

  score.add(StatSource.turret_plates, turret_plates)

  if control_ward_pct > 0.6:
    score.add(StatSource.control_ward_pct, math.floor((control_ward_pct * 10) - 6))
  
  score.add(StatSource.objectives_secured, objectives_secured * 2)
  score.add(StatSource.objectives_stolen, objectives_stolen * 3)


def calculate_teamfights(position, duration, stats, score):
  damage_taken_pm = stats.get(StatName.damage_taken) / duration
  self_mitigated_pm = stats.get(StatName.self_mitigated) / duration
  heal_shield_pm = (stats.get(StatName.ally_heal) + stats.get(StatName.total_ally_shielded)) / duration
  dpm = stats.get(StatName.total_damage_to_champion) / duration
  immobilisations = stats.get(StatName.immobilisations)
  immobilise_and_kill = stats.get(StatName.immobilise_and_kill)

  score.add(StatSource.damage_taken, math.floor(damage_taken_pm / 666))
  score.add(StatSource.self_mitigated, math.floor(self_mitigated_pm / 333))
  score.add(StatSource.heals_and_shields, math.floor((heal_shield_pm ** 0.9) / 45))
  score.add(StatSource.immobilise_and_kill, math.floor(immobilise_and_kill / 5))
  
  if position != "support":
    if dpm >= 600:
      dpm_value = math.floor(dpm // 100) - 5
      score.add(StatSource.dpm, dpm_value)
    elif dpm < 200:
      score.add(StatSource.dpm, -1)

  score.add(StatSource.immobilisations, math.floor(immobilisations / 15))


def calculate_scoreline(position, stats, score):
  kda = stats.get(StatName.kda)
  deaths = stats.get(StatName.deaths)

  if deaths == 0:
    score.add(StatSource.perfect_kda, 3)
  
  if kda < 1:
    score.add(StatSource.kda, -2)
  else:
    score.add(StatSource.kda, math.floor(min(kda, 20) / 2))


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
  multikill = calculate_multikill_score(stats)

  score.add(StatSource.multikill, multikill)
  score.add(StatSource.alcove_kills, alcove_kills)
  score.add(StatSource.heavy_damage_and_survive, heavy_damage_survive * 2)


def calculate_jungle(stats, score):
  baron_kill = stats.get(StatName.baron_kill)
  early_dragon = stats.get(StatName.early_dragon)
  kp = stats.get(StatName.kill_participation)

  score.add(StatSource.barons, baron_kill)

  if early_dragon > 0:
    score.add(StatSource.early_dragon, max(math.floor((480 - early_dragon) / 60), 0))


  if kp >= 0.9:
    score.add(StatSource.kp, 2)
  elif kp < 0.3:
    score.add(StatSource.kp, -2)


def calculate_support(stats, score):
  save_ally = stats.get(StatName.save_ally)
  only_death_in_teamfight_win = stats.get(StatName.only_death_in_teamfight_win)
  kp = stats.get(StatName.kill_participation)

  score.add(StatSource.save_ally, save_ally)
  score.add(StatSource.only_death_in_teamfight_win, only_death_in_teamfight_win)
  
  if kp >= 0.8:
    score.add(StatSource.kp, 2)
  elif kp < 0.3:
    score.add(StatSource.kp, -2)


def calculate_score(game, position, stats, multiplier):
  duration = game.game_duration
  score = ScoreComputer(0, multiplier)

  score.add(StatSource.games, -10)

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