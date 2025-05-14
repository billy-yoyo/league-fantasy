from ..models import Tournament
from .scrape_match import scrape_unloaded_games
from .scrape_match_history import scrape_match_list
from .score_calculator import update_all_player_scores_for_tournament

def daily_refresh_job_for_tournament(tournament):
  print("Fetching latest match list...")
  scrape_match_list(tournament)
  print("Loading unloaded games...")
  scrape_unloaded_games(tournament)
  print("Updating scores...")
  update_all_player_scores_for_tournament(tournament)
  print("Done!")

def daily_refresh_job():
  active_tournament = Tournament.objects.filter(active=True).first()

  if active_tournament is None:
    print("no active tournament")
  else:
   daily_refresh_job_for_tournament(active_tournament)
