from ...scraper.scrape_match import scrape_all_games
from ...scraper.score_calculator import update_all_player_scores_for_tournament
from ...models import Tournament
from django.core.management.base import BaseCommand
from ...scraper.daily_updater import daily_refresh_job_for_tournament

def daily_refresh_job():
  active_tournament = Tournament.objects.filter(active=True).first()
  daily_refresh_job_for_tournament(active_tournament)

class Command(BaseCommand):
  help = "Refresh game data."

  def handle(self, *args, **options):
    daily_refresh_job()
  