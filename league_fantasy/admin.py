from django.contrib import admin
from .models import Tournament, Season, Team, Player, Game, UserDraft
from .scraper.scrape_games import update_game_data_for_tournament, update_game_data_for_season, refresh_game_data_for_season, refresh_game_data_for_tournament
from .scraper.scrape_teams import get_teams_and_players_for_tournament
from .scraper.score_calculator import update_all_player_scores_for_season, update_all_player_scores_for_tournament

@admin.action(description="Refresh team and player data")
def refresh_team_and_player_data_for_tournament(modeladmin, request, queryset):
  for tournament in queryset:
    get_teams_and_players_for_tournament(tournament)

@admin.action(description="Update game stat data")
def update_game_stat_data_for_tournament(modeladmin, request, queryset):
  for tournament in queryset:
    update_game_data_for_tournament(tournament)

@admin.action(description="Refresh game stat data")
def refresh_game_stat_data_for_tournament(modeladmin, request, queryset):
  for tournament in queryset:
    refresh_game_data_for_tournament(tournament)

@admin.action(description="Recalculate scores")
def recalculate_scores_for_tournament(modeladmin, request, queryset):
  for tournament in queryset:
    update_all_player_scores_for_tournament(tournament)

@admin.action(description="Update game stat data")
def update_game_stat_data_for_season(modeladmin, request, queryset):
  for season in queryset:
    update_game_data_for_season(season)

@admin.action(description="Refresh game stat data")
def refresh_game_stat_data_for_season(modeladmin, request, queryset):
  for season in queryset:
    refresh_game_data_for_season(season)

@admin.action(description="Recalculate scores")
def recalculate_scores_for_season(modeladmin, request, queryset):
  for season in queryset:
    update_all_player_scores_for_season(season)

@admin.action(description="Daily refresh")
def daily_refresh(modeladmin, request, queryset):
  for season in queryset:
    update_game_data_for_season(season)
    update_all_player_scores_for_season(season)

class TournamentAdmin(admin.ModelAdmin):
  actions = [
    refresh_team_and_player_data_for_tournament,
    update_game_stat_data_for_tournament,
    refresh_game_stat_data_for_tournament,
    recalculate_scores_for_tournament
  ]
  list_display = ["name", "season"]

class SeasonAdmin(admin.ModelAdmin):
  actions = [
    update_game_stat_data_for_season,
    refresh_game_stat_data_for_season,
    recalculate_scores_for_season,
    daily_refresh
  ]
  list_display = ["name"]

class TeamAdmin(admin.ModelAdmin):
  list_display = ["short_name", "full_name", "team_id"]

class PlayerAdmin(admin.ModelAdmin):
  list_display = ["in_game_name", "score", "team", "position", "player_id", "active"]

class GameAdmin(admin.ModelAdmin):
  list_display = ["game_id", "team_a", "team_b", "winner", "tournament"]

class UserDraftAdmin(admin.ModelAdmin):
  list_display = ["user", "score"]


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Season, SeasonAdmin)

admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(UserDraft, UserDraftAdmin)
