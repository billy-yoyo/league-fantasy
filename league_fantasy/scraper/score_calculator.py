from ..models import Player, Game, PlayerStat

def calculate_score(stats):
  print(stats)
  return 0

def update_player_score(player_id, tournament):
  try:
    player = Player.objects.get(player_id=player_id)
  except:
    raise Exception(f"no such player {player_id}")

  stats = {}
  for stat in PlayerStat.objects.filter(game__tournament__name=tournament).filter(player__player_id=player_id):
    stats[stat.stat_name] = stat.stat_value
  
  player.score = calculate_score(stats)
  player.save()

def update_all_player_scores(tournament):
  for player in Player.objects.all():
    update_player_score(player.player_id, tournament)
 

