from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import UserDraft, UserDraftPlayer, UserDraftScorePoint, Leaderboard, LeaderboardMember, PlayerTournamentScore
from collections import defaultdict
from dataclasses import dataclass
from .graphing.group_by_time import group_data_by_day
from .helper import authorized, get_tournament
import traceback

@authorized
def create_leaderboard(request):
  name = request.POST.get("name", None)
  if name is None:
      return HttpResponseRedirect(f"/leaderboards?error=true")
  
  name = name.strip()
  if not name:
      return HttpResponseRedirect(f"/leaderboards?error=true")
  
  leaderboard = Leaderboard(name=name)
  leaderboard.save()
  LeaderboardMember(user=request.user, leaderboard=leaderboard, is_admin=True).save()
  return HttpResponseRedirect(f"/leaderboards")

def perform_membership_action(request, leaderboard_id, action):
  if leaderboard_id is None:
    return HttpResponseRedirect(f"/leaderboards")
  
  leaderboard = Leaderboard.objects.filter(id=leaderboard_id).first()
  if leaderboard is None:
    return HttpResponseRedirect(f"/leaderboards")
  
  admin_membership = LeaderboardMember.objects.filter(user=request.user).filter(leaderboard=leaderboard).first()
  if admin_membership is None or not admin_membership.is_admin:
    return HttpResponseRedirect(f"/leaderboards")
      
  username = request.POST.get("name", None)
  if username is None:
      return HttpResponseRedirect(f"/leaderboard/{leaderboard_id}/manage?error=true")
  
  user = get_user_model().objects.filter(username=username).first()
  if user is None:
      return HttpResponseRedirect(f"/leaderboard/{leaderboard_id}/manage?error=true")

  membership = LeaderboardMember.objects.filter(user=user).filter(leaderboard=leaderboard).first()
  action(leaderboard, user, membership)
    
  return HttpResponseRedirect(f"/leaderboard/{leaderboard_id}/manage")

@authorized
def add_leaderboard_member(request, leaderboard_id=None):
  def create(leaderboard, user, membership):
    if membership is None:
      LeaderboardMember(user=user, leaderboard=leaderboard, is_admin=False).save()

  return perform_membership_action(request,leaderboard_id, create)

@authorized
def kick_leaderboard_member(request, leaderboard_id=None):
  def kick(_, __, membership):
      if membership:
          membership.delete()

  return perform_membership_action(request, leaderboard_id, kick)

@authorized
def promote_leaderboard_member(request, leaderboard_id=None):
  def promote(_, __, membership):
      if membership:
          membership.is_admin = True
          membership.save()

  return perform_membership_action(request, leaderboard_id, promote)

@authorized
def demote_leaderboard_member(request, leaderboard_id=None):
  def demote(_, user, membership):
      if membership and user.username != request.user.username:
          membership.is_admin = False
          membership.save()

  return perform_membership_action(request, leaderboard_id, demote)

@authorized
def delete_leaderboard(request, leaderboard_id=None):
  if leaderboard_id is None:
    return HttpResponseRedirect(f"/leaderboards")
  
  leaderboard = Leaderboard.objects.filter(id=leaderboard_id).first()
  if leaderboard is None:
    return HttpResponseRedirect(f"/leaderboards")
  
  admin_membership = LeaderboardMember.objects.filter(user=request.user).filter(leaderboard=leaderboard).first()
  if admin_membership is None or not admin_membership.is_admin:
    return HttpResponseRedirect(f"/leaderboards")
  
  LeaderboardMember.objects.filter(leaderboard=leaderboard).delete()
  leaderboard.delete()
  
  return HttpResponseRedirect(f"/leaderboards")

@authorized
def manage_leaderboard(request, leaderboard_id=None):
  if leaderboard_id is None:
    return HttpResponseRedirect(f"/leaderboards")
  
  leaderboard = Leaderboard.objects.filter(id=leaderboard_id).first()
  if leaderboard is None:
    return HttpResponseRedirect(f"/leaderboards")
  
  admin_membership = LeaderboardMember.objects.filter(user=request.user).filter(leaderboard=leaderboard).first()
  if admin_membership is None or not admin_membership.is_admin:
    return HttpResponseRedirect(f"/leaderboards")
  
  members = LeaderboardMember.objects.filter(leaderboard=leaderboard).all()

  return render(request, "manage_leaderboard_page.html", {
    "leaderboard": leaderboard,
    "members": members,
    "error": bool(request.GET.get("error", None))
  })

@authorized
def all_draft_leaderboards(request):
    memberships = LeaderboardMember.objects.filter(user=request.user).all()
    leaderboards = [m.leaderboard for m in memberships]
    return render(request, "all_draft_leaderboards_page.html", { "leaderboards": leaderboards })

GRAPH_DATA_POINTS = 30
@dataclass
class DraftPlayerData:
    name: str
    score: int
    score_percent: float
    team_url: str
    team_background_colour: str
    id: str

@authorized
def draft_leaderboard(request, leaderboard_id=None):
  print("getting draft leaderboard")
  try:
      tournament = get_tournament(request)

      leaderboard = None
      if leaderboard_id is None:
          memberships = LeaderboardMember.objects.filter(user=request.user).all()
          if len(memberships) == 1:
              return HttpResponseRedirect(f"/leaderboard/{memberships[0].leaderboard.id}")
      else:
          membership = LeaderboardMember.objects.filter(user=request.user).filter(leaderboard__id=leaderboard_id).first()
          if membership is not None:
              leaderboard = membership.leaderboard
      
      if leaderboard is None:
          return HttpResponseRedirect("/leaderboards")

      members = [lm.user for lm in LeaderboardMember.objects.filter(leaderboard=leaderboard).all()]
      membership = LeaderboardMember.objects.filter(user=request.user).filter(leaderboard=leaderboard).first()
      if membership is None:
          return HttpResponseRedirect("/leaderboards")
      
      drafts = UserDraft.objects.filter(user__in=members).order_by("-score").all()
      draft_players = defaultdict(dict)
      user_colours = defaultdict(lambda: "#000000")
      positions = ("top", "jungle", "mid", "bot", "support")
      player_scores = {}

      for draft in drafts:
          draft.partial_score = draft.score - draft.score_offset
          for player in UserDraftPlayer.objects.filter(draft=draft):
              if player.id not in player_scores:
                tournament_score = PlayerTournamentScore.objects.filter(player=player.player, tournament=tournament).first()
                player_scores[player.id] = tournament_score.score if tournament_score else player.player.score
              
              draft_players[draft.user.username][player.player.position] = DraftPlayerData(
                  name=f"{player.player.team.short_name} {player.player.in_game_name}",
                  score=player_scores[player.id],
                  score_percent=player_scores[player.id] * 100 / max(draft.partial_score, 1),
                  team_url=player.player.team.icon_url,
                  team_background_colour=player.player.team.background_colour,
                  id=str(player.player.id)
              )
              user_colours[draft.user.username] = draft.colour

          if all(position not in draft_players[draft.user.username] for position in positions):
            del draft_players[draft.user.username]
            continue 

          for position in positions:
              if position not in draft_players[draft.user.username]:
                  draft_players[draft.user.username][position] = DraftPlayerData(
                    name="---",
                    score=0,
                    score_percent=0,
                    team_url="",
                    team_background_colour="#fff",
                    id="---"
                  )



      labels, raw_datasets = group_data_by_day(
        UserDraftScorePoint.objects.filter(draft__in=drafts).order_by("-time"),
        GRAPH_DATA_POINTS,
        lambda x: x.draft.user.username
      )

      datasets = [{
        "label": username,
        "data": data,
        "fill": False,
        "borderColor": user_colours[username],
        "tension": 0.1
      } for username, data in raw_datasets]

      graph_data = {
          "labels": labels,
          "datasets": datasets
      }

      return render(request, "draft_leaderboard_page.html", {
          "drafts": [draft for draft in drafts if draft.user.username in draft_players],
          "positions": positions,
          "draft_players": draft_players,
          "graph_data": graph_data,
          "leaderboard": leaderboard,
          "is_admin": membership.is_admin
      })
  except Exception:
    print(traceback.format_exc())

