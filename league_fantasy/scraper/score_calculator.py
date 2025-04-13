from ..models import Player, Tournament, PlayerStat, Game, UserDraft, UserDraftPlayer, UserDraftScorePoint, PlayerScorePoint, GamePlayer, PlayerTournamentScore
from .statistics.stats import StatName
from datetime import datetime
from .score_computer import ScoreComputer
from .statistics.new_score_calculator import calculate_score as new_calculate_score
import math
from collections import defaultdict

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

def count_match_stats(games):
  match_wins = defaultdict(lambda: defaultdict(int))
  for game in games:
    if game.match_id:
      match_wins[game.match_id][game.winner] += 1
  
  match_multipliers = defaultdict(int)
  for match_id, win_counts in match_wins.items():
    max_wins = max(win_counts.values())
    total_wins = sum(win_counts.values())
    match_multipliers[match_id] = max_wins / total_wins
  
  return match_multipliers

def get_player_score_sources_per_game_for_tournament(player, tournament):
  game_scores = []
  games = [game for game in Game.objects.filter(tournament=tournament).order_by("time")]
  match_multipliers = count_match_stats(games)

  for game in games:
    stats = defaultdict(int)
    for stat in PlayerStat.objects.filter(game=game).filter(player=player).all():
      stats[stat.stat_name] = stat.stat_value
    
    if len(stats) == 0:
      continue
    game_player = GamePlayer.objects.filter(game=game, player=player).first()
    position = player.position
    if game_player:
      position = game_player.position
    game_score = new_calculate_score(game, position, stats, match_multipliers.get(game.match_id, 1))
    game_scores.append((game, game_score))
  return sorted(game_scores, key=lambda x: x[0].time)

def get_player_stats(game, player):
  stats = defaultdict(int)
  for stat in PlayerStat.objects.filter(game=game).filter(player=player):
    stats[stat.stat_name] = stat.stat_value
  return stats

def get_player_game_score(player, game):
  stats = get_player_stats(game, player)
  game_player = GamePlayer.objects.filter(game=game, player=player).first()
  position = player.position
  if game_player:
    position = game_player.position
  
  return new_calculate_score(game, position, stats, 1)

def get_champion_score_per_game(tournament, champion_id):
  player_stats = PlayerStat.objects.filter(game__tournament=tournament).filter(stat_name=StatName.champion_id).filter(stat_value=champion_id)
  game_scores = []
  for stat in player_stats:
    game_score = get_player_game_score(stat.player, stat.game)
    game_scores.append((stat.game, game_score))
  return sorted(game_scores, key=lambda x: x[0].time)

def update_player_score(tournament_player, time):
  player = tournament_player.player
  tournament = tournament_player.tournament
  games = [game for game in Game.objects.filter(tournament=tournament).order_by("time")]
  match_multipliers = count_match_stats(games)

  score = ScoreComputer(0)
  total_games = 0
  for game in games:
    stats = get_player_stats(game, player)
    if len(stats) == 0:
      continue
    game_player = GamePlayer.objects.filter(game=game, player=player).first()
    position = player.position
    if game_player:
      position = game_player.position
    game_score = new_calculate_score(game, position, stats, match_multipliers.get(game.match_id, 1))
    score.merge(game_score)
    total_games += 1

  if tournament.active:
    player.score = score.score
    player.save()

  PlayerScorePoint(player=player, score=score.score, time=time).save()

  tournament_player.score = score.score
  tournament_player.save()

def update_user_draft(user_draft, time):
  score = 0
  for player in UserDraftPlayer.objects.filter(draft=user_draft):
    score += player.player.score

  score += user_draft.score_offset
  
  user_draft.score = score
  user_draft.save()

  UserDraftScorePoint(draft=user_draft, score=score, time=time).save()

def update_all_user_drafts(time):
  for user_draft in UserDraft.objects.all():
    update_user_draft(user_draft, time)

def update_all_player_scores_for_tournament(tournament):
  time = datetime.now()
  for tournament_player in PlayerTournamentScore.objects.filter(tournament=tournament):
    update_player_score(tournament_player, time)
  if tournament.active:
    update_all_user_drafts(time)
 

