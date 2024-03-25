from django.contrib import admin
from .models import Tournament
from .scraper.scrape_games import update_game_data, refresh_game_data
from .scraper.scrape_teams import get_teams_and_players
from .scraper.score_calculator import update_all_player_scores

@admin.action(description="Refresh team and player data")
def refresh_team_and_player_data(modeladmin, request, queryset):
  for tournament in queryset:
    get_teams_and_players(tournament.name)

@admin.action(description="Update game stat data")
def update_game_stat_data(modeladmin, request, queryset):
  for tournament in queryset:
    update_game_data(tournament.name)

@admin.action(description="Refresh game stat data")
def refresh_game_data(modeladmin, request, queryset):
  for tournament in queryset:
    refresh_game_data(tournament.name)

@admin.action(description="Recalculate scores")
def recalculate_scores(modeladmin, request, queryset):
  for tournament in queryset:
    update_all_player_scores(tournament.name)

@admin.action(description="Daily refresh")
def daily_refresh(modeladmin, request, queryset):
  for tournament in queryset:
    update_game_data(tournament.name)
    update_all_player_scores(tournament.name)

class TournamentAdmin(admin.ModelAdmin):
  actions = [daily_refresh, refresh_team_and_player_data, update_game_stat_data, refresh_game_data, recalculate_scores]
  list_display = ["name"]

admin.site.register(Tournament, TournamentAdmin)
