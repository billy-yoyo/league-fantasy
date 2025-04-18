"""
URL configuration for league_fantasy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView 
from django.conf.urls.static import static
from django.conf import settings

import league_fantasy.views as views
import league_fantasy.leaderboard_views as leaderboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('', views.home),
    path("players/", views.player_leaderboard),
    path("players/<int:player_id>/", views.player_graph),
    path("champions/", views.champion_grid),
    path("champions/<int:champion_id>/", views.champion_graph),
    path("draft/", views.draft),
    path("submit-draft/", views.submit_draft),
    path("logout/", views.logout_view),
    path("accounts/profile/", views.profile),
    path("stat/<slug:stat_source>", views.stats_page),
    path("game/<int:game_id>", views.game_page),
    path("leaderboard/", leaderboard_views.draft_leaderboard),
    path("leaderboards/", leaderboard_views.all_draft_leaderboards),
    path("leaderboards/create", leaderboard_views.create_leaderboard),
    path("leaderboard/<int:leaderboard_id>", leaderboard_views.draft_leaderboard),
    path("leaderboard/<int:leaderboard_id>/manage", leaderboard_views.manage_leaderboard),
    path("leaderboard/<int:leaderboard_id>/manage/invite", leaderboard_views.add_leaderboard_member),
    path("leaderboard/<int:leaderboard_id>/manage/kick", leaderboard_views.kick_leaderboard_member),
    path("leaderboard/<int:leaderboard_id>/manage/promote", leaderboard_views.promote_leaderboard_member),
    path("leaderboard/<int:leaderboard_id>/manage/demote", leaderboard_views.demote_leaderboard_member),
    path("leaderboard/<int:leaderboard_id>/manage/delete", leaderboard_views.delete_leaderboard),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
