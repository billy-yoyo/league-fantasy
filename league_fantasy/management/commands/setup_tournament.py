

from ...models import Player, PlayerTournamentScore, Tournament
from django.core.management.base import BaseCommand, CommandParser
from datetime import datetime

format = "%Y-%m-%d"

class Command(BaseCommand):
  help = "Setup a new tournament."
  
  def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("new", type=str)
    parser.add_argument("old", type=str)

  def handle(self, *args, **options):
    new_tournament_id = options["new"]
    old_tournament_id = options["old"]

    new_tournament = Tournament.objects.filter(id=new_tournament_id).first()
    old_tournament = Tournament.objects.filter(id=old_tournament_id).first()

    new_tournament_players = []
    player_updates = []
    for tournament_player in PlayerTournamentScore.objects.filter(tournament=old_tournament).all():
      new_tournament_players.append(PlayerTournamentScore(player=tournament_player.player, tournament=new_tournament, score=0))
      player_updates.append(tournament_player.player)
      tournament_player.player.score = 0
    
    PlayerTournamentScore.objects.bulk_create(new_tournament_players)
    Player.objects.bulk_update(player_updates, ["score"])


