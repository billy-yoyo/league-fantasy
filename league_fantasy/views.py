from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from .scraper.scrape_teams import get_teams_and_players_for_tournament
from .models import Player, UserDraft, UserDraftPlayer, UserDraftScorePoint, PlayerScorePoint
from collections import defaultdict
from django.contrib.auth import logout

TOURNAMENT = "LEC Spring Season 2024"

def refresh_teams_and_players(request):
    [teams, players] = get_teams_and_players_for_tournament(TOURNAMENT)

    lines = []
    lines.append("<h2>Teams:</h2><ul>")
    for team in teams:
        lines.append(f"<li>{team.team_id}, {team.full_name}, {team.short_name}</li>")

    lines.append("</ul>")
    lines.append("<h2>Players:</h2><ul>")
    for player in players:
        lines.append(f"<li>{player.player_id}, {player.in_game_name}, {player.country}, {player.position}, {player.score}</li>")
    lines.append("</ul>")

    return HttpResponse("\n".join(lines))

def refresh_matches(request):
    return HttpResponse("Done")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")

def profile(request):
    return HttpResponseRedirect("/")

def home(request):
    return HttpResponseRedirect("/leaderboard")

def player_leaderboard(request):
    players = Player.objects.filter(active=True).order_by("-score").all()
    positions = ("top", "jungle", "mid", "bot", "support")
    return render(request, "player_page.html", { "players": players, "positions": positions })

GRAPH_DATA_POINTS = 10

def draft_leaderboard(request):
    drafts = UserDraft.objects.order_by("-score").all()
    draft_players = defaultdict(dict)
    draft_player_ids = defaultdict(dict)
    positions = ("top", "jungle", "mid", "bot", "support")

    for draft in drafts:
        for player in UserDraftPlayer.objects.filter(draft=draft):
            draft_players[draft.user.username][player.player.position] = f"{player.player.team.short_name} {player.player.in_game_name} ({player.player.score})"
            draft_player_ids[draft.user.username][player.player.position] = player.player.player_id

    time_points = set()

    for score_point in UserDraftScorePoint.objects.order_by("-time"):
        time_points.add(score_point.time)
        if len(time_points) >= GRAPH_DATA_POINTS:
            break

    time_points = sorted(time_points)
    
    labels = [time.strftime("%d:%m:%Y") for time in time_points]
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
        "graph_data": graph_data
    })

def draft(request):
    players = Player.objects.filter(active=True).order_by("-score").all()
    try:
        draft = UserDraft.objects.get(user=request.user)
    except:
        draft = UserDraft(user=request.user, score=0)
        draft.save()

    positions = ("top", "jungle", "mid", "bot", "support")

    position_players = {}

    for draft_player in UserDraftPlayer.objects.filter(draft=draft):
        position_players[draft_player.player.position] = draft_player.player.player_id

    for pos in positions:
        if pos not in position_players:
            position_players[pos] = "none"

    return render(request, "draft_page.html", {
        "players": players,
        "positions": positions,
        "draft": position_players,
        "error": bool(request.GET.get("error", None))
    })

def submit_draft(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    if request.method != "POST":
        return HttpResponse(status_code=404)
    
    post = request.POST.dict()
    player_ids = [
        post.get("position_top"),
        post.get("position_jungle"),
        post.get("position_mid"),
        post.get("position_bot"),
        post.get("position_support"),
    ]

    if any(p is None or p == "none" for p in player_ids):
        return HttpResponseRedirect("/draft?error=true") 

    players = Player.objects.filter(player_id__in=player_ids).all()

    score = 0
    for player in players:
        score += player.score

    try:
        user_draft = UserDraft.objects.get(user=request.user)
    except:
        user_draft = UserDraft(user=request.user, score=score)
        user_draft.save()
    
    UserDraftPlayer.objects.filter(draft=user_draft).delete()

    for player in players:
        UserDraftPlayer(draft=user_draft, player=player).save()

    return HttpResponseRedirect("/draft")

def player_graph(request, player_id=None):
    try:
        player = Player.objects.get(player_id=player_id)
    except:
        return HttpResponseBadRequest()

    time_points = set()

    for score_point in PlayerScorePoint.objects.filter(player=player).order_by("-time"):
        time_points.add(score_point.time)
        if len(time_points) >= GRAPH_DATA_POINTS:
            break

    time_points = sorted(time_points)
    
    labels = [time.strftime("%d:%m:%Y") for time in time_points]
    data = []
    for time in time_points:
        try:
            score_point = PlayerScorePoint.objects.get(player=player, time=time)
            data.append(score_point.score)
        except:
            data.append(0)
    
    dataset = {
        "label": "",
        "data": data,
        "fill": False,
        "borderColor": "#dedede",
        "tension": 0.1
    }

    graph_data = {
        "labels": labels,
        "datasets": [dataset]
    }

    return render(request, "player_graph_page.html", {
        "player": player,
        "player_name": f"{player.team.short_name} {player.in_game_name}",
        "graph_data": graph_data
    })
