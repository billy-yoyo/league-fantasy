from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from .scraper.score_calculator import get_player_score_sources_per_game_for_active_tournament
from .models import Player, UserDraft, UserDraftPlayer, PlayerScorePoint
from django.contrib.auth import logout
from .graphing.group_by_time import group_data_by_day
from .helper import authorized

def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")

def profile(request):
    return HttpResponseRedirect("/")

def home(request):
    return HttpResponseRedirect("/leaderboard")

@authorized
def player_leaderboard(request):
    players = Player.objects.filter(active=True).order_by("-score").all()
    positions = ("top", "jungle", "mid", "bot", "support")
    return render(request, "player_page.html", { "players": players, "positions": positions })

GRAPH_DATA_POINTS = 10

@authorized
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
        position_players[draft_player.player.position] = draft_player.player.id

    for pos in positions:
        if pos not in position_players:
            position_players[pos] = "none"

    return render(request, "draft_page.html", {
        "players": players,
        "positions": positions,
        "draft": position_players,
        "error": bool(request.GET.get("error", None))
    })

@authorized
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
        user_draft.score = score
        user_draft.save()
    except:
        user_draft = UserDraft(user=request.user, score=score)
        user_draft.save()
    
    UserDraftPlayer.objects.filter(draft=user_draft).delete()

    for player in players:
        UserDraftPlayer(draft=user_draft, player=player).save()

    return HttpResponseRedirect("/draft")

@authorized
def player_graph(request, player_id=None):
    try:
        player = Player.objects.get(id=player_id)
    except:
        return HttpResponseBadRequest()
    
    game_scores = get_player_score_sources_per_game_for_active_tournament(player)
    game_names = [
        (game.team_a.short_name, game.team_a.id == game.winner,
         game.team_b.short_name, game.team_b.id == game.winner) for game, _ in game_scores
    ]
    scores = [score for _, score in game_scores]

    sources = set()
    for score in scores:
        sources |= set(score.score_sources.keys())
    sources = list(sorted(sources))
    sources = [(source, source.replace("_", " ").title()) for source in sources]

    source_totals = {}
    for source, _ in sources:
        source_totals[source] = sum(score.get(source) for score in scores)

    labels, raw_datasets = group_data_by_day(
        PlayerScorePoint.objects.filter(player=player).order_by("-time"),
        GRAPH_DATA_POINTS,
        lambda x: x.player.id
    )
    
    datasets = [{
        "label": "",
        "data": data,
        "fill": False,
        "borderColor": "#dedede",
        "tension": 0.1
    } for _, data in raw_datasets]

    graph_data = {
        "labels": labels,
        "datasets": datasets
    }

    return render(request, "player_graph_page.html", {
        "player": player,
        "player_name": f"{player.team.short_name} {player.in_game_name}",
        "graph_data": graph_data,
        "sources": sources,
        "scores": scores,
        "game_names": game_names,
        "source_totals": source_totals,
        "colspan": len(game_names) + 1
    })


