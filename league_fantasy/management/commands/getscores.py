

from ...models import PlayerTournamentScore, GamePlayer
from django.core.management.base import BaseCommand, CommandParser
from datetime import datetime
import csv

format = "%Y-%m-%d"

class Command(BaseCommand):
  help = "Get Player Costs."
  
  def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("--csv", type=str)
    parser.add_argument("--tournament", type=int)

  def handle(self, *args, **options):
    csv_file = options["csv"]
    tournamnet_id = options["tournament"]

    rows = []
    for player in PlayerTournamentScore.objects.filter(tournament__id=tournamnet_id).all():
      games = GamePlayer.objects.filter(player=player.player, game__tournament__id=tournamnet_id).count()
      rows.append([player.player.in_game_name.lower(), player.score, games])

    with open(csv_file, "w", newline="") as f:
      writer = csv.writer(f)
      writer.writerows(rows)

  