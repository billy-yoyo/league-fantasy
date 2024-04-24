



from ...models import PlayerTournamentScore
from django.core.management.base import BaseCommand, CommandParser
from datetime import datetime
import csv
import math

format = "%Y-%m-%d"

def compute_simple_score(pd):
  games = float(pd["g"])
  wins = float(pd["w"])
  losses = float(pd["l"])
  kills = float(pd["k"])
  deaths = float(pd["d"])
  assists = float(pd["a"])
  kda = float(pd["kda"])
  kp = float(pd["kp%"])
  kill_share = float(pd["ks%"])
  cs = float(pd["cs"])
  csm = float(pd["csm"])
  gold_share = float(pd["gld%"])
  dpm = float(pd["dpm"])
  first_blood = float(pd["fb"])
  ward_pm = float(pd["wpm"])
  ward_clear_pm = float(pd["wcpm"])

  score = 0
  score += max(0, math.floor(csm - 8))
  score += first_blood
  score += (ward_pm + ward_clear_pm) * 4
  if dpm < 200:
    score -= 1
  elif dpm >= 600:
    score += math.floor((dpm - 400) // 200)
  if kda < 1:
    score -= -2
  else:
    score += math.floor(min(kda, 20) / 2)
  if kp >= 80:
    score += 2
  elif kp < 30:
    score -= 1
  if gold_share > 35:
    score += math.floor((gold_share - 35) / 5)

  return score


class Command(BaseCommand):
  help = "Update Player Costs."
  
  def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("--tournament", type=int)
    parser.add_argument("--in", type=str)
    parser.add_argument("--out", type=str)

  def handle(self, *args, **options):
    tournament = options["tournament"]
    csv_file = options["in"]
    out_file = options["out"]

    with open(csv_file, "r", newline="") as f:
      reader = csv.reader(f)
      header = next(reader)
      data = []
      for row in reader:
        data.append({k.lower(): v for k, v in zip(header, row)})
    
    valid_player_names = []
    for player in PlayerTournamentScore.objects.filter(tournament__id=tournament):
      valid_player_names.append(player.player.in_game_name.lower())

    out_data = []
    for player in data:
      if player["player"].lower() in valid_player_names:
        out_data.append([player["player"], compute_simple_score(player)])
    
    out_data.sort(key=lambda x: x[1], reverse=True)

    with open(out_file, "w", newline="") as f:
      writer = csv.writer(f)
      writer.writerows(out_data)
    

        
    
    

  