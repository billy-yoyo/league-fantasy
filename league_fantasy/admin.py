from django.contrib import admin
from .models import Tournament, Season, Team, Player, Game, UserDraft, UserDraftPlayer, Leaderboard, LeaderboardMember, PlayerSynonym, PlayerTournamentScore
from .scraper.scrape_match_history import scrape_match_list
from .scraper.scrape_match import scrape_match
from .scraper.score_calculator import update_all_player_scores_for_tournament
from .scraper.daily_updater import daily_refresh_job_for_tournament

@admin.action(description="Update match list")
def update_tournament_match_list(modeladmin, request, queryset):
  for tournament in queryset:
    scrape_match_list(tournament)

@admin.action(description="Recalculate scores")
def recalculate_scores_for_tournament(modeladmin, request, queryset):
  for tournament in queryset:
    update_all_player_scores_for_tournament(tournament)

@admin.action(description="Post-Game Refresh")
def post_game_refresh(modeladmin, request, queryset):
  for tournament in queryset:
    daily_refresh_job_for_tournament(tournament)

@admin.action(description="Update game statistics")
def update_game_statistics(modeladmin, request, queryset):
  for game in queryset:
    scrape_match(game)

class TournamentAdmin(admin.ModelAdmin):
  actions = [
    update_tournament_match_list,
    recalculate_scores_for_tournament,
    post_game_refresh
  ]
  list_display = ["id", "name", "disambig_name", "season", "active"]

class SeasonAdmin(admin.ModelAdmin):
  list_display = ["name"]

class TeamAdmin(admin.ModelAdmin):
  list_display = ["id", "short_name", "full_name"]

class PlayerAdmin(admin.ModelAdmin):
  list_display = ["id", "in_game_name", "score", "team", "position", "active"]

class PlayerSynonymAdmin(admin.ModelAdmin):
  list_display = ["name", "player"]

class PlayerTournamentScoreAdmin(admin.ModelAdmin):
  list_display = ["player", "tournament", "score"]


class GameAdmin(admin.ModelAdmin):
  actions = [
    update_game_statistics
  ]
  list_display = ["id", "rpgid", "team_a", "team_b", "winner", "time", "tournament", "statistics_loaded"]

class UserDraftAdmin(admin.ModelAdmin):
  list_display = ["user", "score"]

class UserDraftPlayerAdmin(admin.ModelAdmin):
  list_display = ["draft", "player"]

class LeaderboardAdmin(admin.ModelAdmin):
  list_display = ["id", "name"]

class LeaderboardMemberAdmin(admin.ModelAdmin):
  list_display = ["user", "leaderboard", "is_admin"]

admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Season, SeasonAdmin)

admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(PlayerSynonym, PlayerSynonymAdmin)
admin.site.register(PlayerTournamentScore, PlayerTournamentScoreAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(UserDraft, UserDraftAdmin)
admin.site.register(UserDraftPlayer, UserDraftPlayerAdmin)
admin.site.register(Leaderboard, LeaderboardAdmin)
admin.site.register(LeaderboardMember, LeaderboardMemberAdmin)
