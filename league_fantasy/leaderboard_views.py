from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import UserDraft, UserDraftPlayer, UserDraftScorePoint, Leaderboard, LeaderboardMember
from collections import defaultdict

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

def add_leaderboard_member(request, leaderboard_id=None):
  def create(leaderboard, user, membership):
    if membership is None:
      LeaderboardMember(user=user, leaderboard=leaderboard, is_admin=False).save()

  return perform_membership_action(request,leaderboard_id, create)

def kick_leaderboard_member(request, leaderboard_id=None):
  def kick(_, __, membership):
      if membership:
          membership.delete()

  return perform_membership_action(request, leaderboard_id, kick)

def promote_leaderboard_member(request, leaderboard_id=None):
  def promote(_, __, membership):
      if membership:
          membership.is_admin = True
          membership.save()

  return perform_membership_action(request, leaderboard_id, promote)

def demote_leaderboard_member(request, leaderboard_id=None):
  def demote(_, user, membership):
      if membership and user.username != request.user.username:
          membership.is_admin = False
          membership.save()

  return perform_membership_action(request, leaderboard_id, demote)

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

def all_draft_leaderboards(request):
    memberships = LeaderboardMember.objects.filter(user=request.user).all()
    leaderboards = [m.leaderboard for m in memberships]
    return render(request, "all_draft_leaderboards_page.html", { "leaderboards": leaderboards })

GRAPH_DATA_POINTS = 10

def draft_leaderboard(request, leaderboard_id=None):
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
    draft_player_ids = defaultdict(dict)
    positions = ("top", "jungle", "mid", "bot", "support")

    for draft in drafts:
        for player in UserDraftPlayer.objects.filter(draft=draft):
            draft_players[draft.user.username][player.player.position] = f"{player.player.team.short_name} {player.player.in_game_name} ({player.player.score})"
            draft_player_ids[draft.user.username][player.player.position] = player.player.player_id
        for position in positions:
            if position not in draft_players[draft.user.username]:
                draft_players[draft.user.username][position] = "---"
                draft_player_ids[draft.user.username][position] = ""

    time_points = set()

    for score_point in UserDraftScorePoint.objects.filter(draft__in=drafts).order_by("-time"):
        time_points.add(score_point.time)
        if len(time_points) >= GRAPH_DATA_POINTS:
            break

    time_points = sorted(time_points)
    
    labels = [time.strftime("%d/%m/%Y") for time in time_points]
    datasets = []
    for draft in drafts:
        data = []
        for time in time_points:
            try:
                score_point = UserDraftScorePoint.objects.get(draft=draft, time=time)
                data.append(score_point.score)
            except:
                data.append(0)
        datasets.append({
            "label": draft.user.username,
            "data": data,
            "fill": False,
            "borderColor": draft.colour,
            "tension": 0.1
        })

    graph_data = {
        "labels": labels,
        "datasets": datasets
    }

    return render(request, "draft_leaderboard_page.html", {
        "drafts": drafts,
        "positions": positions,
        "draft_players": draft_players,
        "draft_player_ids": draft_player_ids,
        "graph_data": graph_data,
        "leaderboard": leaderboard,
        "is_admin": membership.is_admin
    })
