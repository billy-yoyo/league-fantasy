

from ...models import PlayerTournamentScore, Tournament
from django.core.management.base import BaseCommand, CommandParser
from datetime import datetime
import csv

format = "%Y-%m-%d"

class Command(BaseCommand):
  help = "Update Player Costs."
  
  def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("--csv", type=str)
    parser.add_argument("--tournament", type=int)

  def handle(self, *args, **options):
    csv_file = options["csv"]
    tournament_id = options["tournament"]
    tournament = Tournament.objects.filter(id=tournament_id).first()
    if not tournament:
      raise Exception(f"Invalid tournament id: {tournament_id}")

    updates = []
    with open(csv_file, "r", newline="") as f:
      for row in csv.reader(f):
        player_name, cost = row
        player = PlayerTournamentScore.objects.filter(tournament=tournament).filter(player__in_game_name__iexact=player_name).first()
        if player:
          player.cost = cost
          updates.append(player)
        else:
          print(f"Failed to find player {player_name}")

    print(f"Updating {len(updates)} players...")
    PlayerTournamentScore.objects.bulk_update(updates, ["cost"])

  