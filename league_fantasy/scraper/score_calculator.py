from ..models import Player, Tournament, PlayerStat, Game, UserDraft, UserDraftPlayer, UserDraftScorePoint, PlayerScorePoint
from .stats import StatName
import math
from collections import defaultdict
from datetime import datetime

class ScoreComputer:
  def __init__(self, score):
    self.score = score
    self.score_sources = defaultdict(int)
  
  def get(self, source):
    return self.score_sources.get(source, 0)

  def add(self, name, value):
    self.score += value
    self.score_sources[name] += value

  def merge(self, score):
    self.score += score.score
    for name, value in score.score_sources.items():
      self.score_sources[name] += value

  def summary(self, name):
    lines = [f"Score for {name} was {self.score}:"]
    for name, value in sorted(self.score_sources.items()):
      lines.append(f"    {name}: {value}")
    return "\n".join(lines)
  
  def __contains__(self, item):
    return item in self.score_sources

def calculate_kda_score(position, stats):
  kda = stats.get(StatName.kda, 0)
  deaths = stats.get(StatName.deaths, 0)

  # perfect kda gives max score here
  if deaths == 0:
    kda = 999

  if position == "support":
    return 0
  else:
    if kda < 1:
      return -2
    elif kda < 5:
      return 1
    elif kda < 10:
      return 2
    else:
      return 5

def calculate_kill_participation_score(position, stats):
  scores = [-3, -2, -1, 0, 0, 1, 2, 3, 4, 5, 8]
  if position == "support" or position == "jungle":
    scores = [-5, -4, -3, -2, -1, 0, 2, 4, 6, 8, 10]

  kp = stats.get(StatName.kill_participation, 0)
  return scores[math.floor(kp * 10)]

def calculate_multikill_score(position, stats):
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

  return doubles + (triples * 3) + (quadras * 5) + (pentas * 10)

def calculate_support_score(game_length_minutes, stats):
  assists = stats.get(StatName.assists, 0)
  deaths = stats.get(StatName.deaths, 0)
  support_score = math.floor((assists - (deaths / 2)) * 15 // game_length_minutes)
  return support_score

def calculate_score_for_game(game, position, stats):
  game_length_minutes = game.game_duration

  score = ScoreComputer(0)

  score.add("games", -10)

  score.add("kda", calculate_kda_score(position, stats))
  score.add("kp", calculate_kill_participation_score(position, stats))
  score.add("multikill", calculate_multikill_score(position, stats))

  if position == "support":
    score.add("support", calculate_support_score(game_length_minutes, stats))

  gold_diff_15 = stats.get(StatName.gold_diff_15, 0)
  xp_diff_15 = stats.get(StatName.xp_diff_15, 0)
  dpm = stats.get(StatName.total_damage_to_champion, 0) / game_length_minutes
  stolen_objectives = stats.get(StatName.objectives_stolen, 0)
  vision_score = stats.get(StatName.vision_score, 0)
  self_mitigated = stats.get(StatName.self_mitigated, 0)
  damage_share = stats.get(StatName.dmg_share, 0) * 100
  turret_damage = stats.get(StatName.turret_damage, 0)
  lost_shutdown = stats.get(StatName.shutdown_lost, 0)
  cspm = stats.get(StatName.cs, 0) / game_length_minutes
  cc_time = stats.get(StatName.cc_time_others, 0)
  damage_taken = stats.get(StatName.damage_taken, 0)
  heals = stats.get(StatName.ally_heal, 0)
  shields = stats.get(StatName.total_ally_shielded, 0)
  solo_kills = stats.get(StatName.solo_kills, 0)
  alcove_kills = stats.get(StatName.alcove_kills, 0)
  turret_plates = stats.get(StatName.turret_plates, 0)

  if gold_diff_15 > 1000:
    score.add("gd15", 3)
  elif gold_diff_15 > 0:
    score.add("gd15", 1)

  if xp_diff_15 > 1000:
    score.add("xp15", 3)
  elif xp_diff_15 > 0:
    score.add("xp15", 1)

  if dpm >= 400:
    score.add("dpm", math.floor(dpm // 200) - 1)
  elif dpm < 200:
    score.add("dpm", -1)

  if damage_share > 30:
    score.add("dmg%", 2)

  if turret_damage > 5000:
    score.add("turret", math.floor((turret_damage - 5000) // 1000))

  if cspm >= 8:
    score.add("cspm", math.floor(cspm - 8))

  if alcove_kills > 0:
    score.add("alcove", alcove_kills)

  score.add("shutdown", -math.floor(lost_shutdown // 300))
  score.add("stolen", stolen_objectives * 5)
  score.add("vision", math.floor(vision_score // game_length_minutes))
  score.add("self_mitigated", math.floor(self_mitigated // (666 * game_length_minutes)))
  score.add("damage_taken", math.floor(damage_taken // (666 * game_length_minutes)))
  score.add("cc", math.floor(cc_time // 13))
  score.add("heals_and_shields", math.floor((heals + shields) // (50 * game_length_minutes)))
  score.add("solo_kills", solo_kills * 2)
  score.add("turret_plates", turret_plates)

  return score

def get_player_score_sources_per_game_for_active_tournament(player):
  game_scores = []
  for game in Game.objects.filter(tournament__active=True).order_by("time"):
    stats = {}
    for stat in PlayerStat.objects.filter(game=game).filter(player=player):
      stats[stat.stat_name] = stat.stat_value
    
    if len(stats) == 0:
      continue
    game_score = calculate_score_for_game(game, player.position, stats)
    game_scores.append((game, game_score))
  return sorted(game_scores, key=lambda x: x[0].time)

def update_player_score(player, tournaments, time):
  score = ScoreComputer(0)
  total_games = 0
  for game in Game.objects.filter(tournament__in=tournaments):
    stats = {}
    for stat in PlayerStat.objects.filter(game=game).filter(player=player):
      stats[stat.stat_name] = stat.stat_value
    if len(stats) == 0:
      continue
    game_score = calculate_score_for_game(game, player.position, stats)
    score.merge(game_score)
    total_games += 1

  player.score = score.score
  player.save()

  PlayerScorePoint(player=player, score=score.score, time=time).save()

def update_user_draft(user_draft, time):
  score = 0
  for player in UserDraftPlayer.objects.filter(draft=user_draft):
    score += player.player.score
  
  user_draft.score = score
  user_draft.save()

  UserDraftScorePoint(draft=user_draft, score=score, time=time).save()

def update_all_user_drafts(time):
  for user_draft in UserDraft.objects.all():
    update_user_draft(user_draft, time)

def update_all_player_scores_for_tournament(tournament):
  time = datetime.now()
  for player in Player.objects.all():
    update_player_score(player, [tournament], time)
  update_all_user_drafts(time)
 
def update_all_player_scores_for_season(season):
  time = datetime.now()
  tournaments = list(Tournament.objects.filter(season=season))
  for player in Player.objects.all():
    update_player_score(player, tournaments, time)
  update_all_user_drafts(time)


