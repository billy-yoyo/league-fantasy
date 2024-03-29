from ...scraper.daily_updater import daily_refresh_job
from django.core.management.base import BaseCommand

class Command(BaseCommand):
  help = "Update game data."

  def handle(self, *args, **options):
    daily_refresh_job()
  