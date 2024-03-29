from ...scraper.scrape_match import scrape_all_games
from ...scraper.score_calculator import update_all_player_scores_for_tournament
from ...models import Tournament
from django.core.management.base import BaseCommand

def daily_refresh_job():
  active_tournament = Tournament.objects.filter(active=True).first()

  if active_tournament is None:
    print("no active tournament")
  else:
    scrape_all_games(active_tournament)
    update_all_player_scores_for_tournament(active_tournament)
    print("updated game data")

class Command(BaseCommand):
  help = "Refresh game data."

  def handle(self, *args, **options):
    daily_refresh_job()
  