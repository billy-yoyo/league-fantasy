from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render
from .scraper.score_calculator import get_player_score_sources_per_game_for_tournament
from .scraper.statistics.stats import ALL_STAT_SOURCES
from .models import Player, UserDraft, UserDraftPlayer, PlayerScorePoint, Game, GamePlayer, PlayerStat, PlayerTournamentScore
from django.contrib.auth import logout
from .graphing.group_by_time import group_data_by_day
from .graphing.bell_curve import create_bell_curve_dataset, create_bell_curve_labels
from .helper import authorized, get_tournament
from collections import defaultdict
from django.db.models import Count

def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")

def profile(request):
    return HttpResponseRedirect("/")

def home(request):
    return HttpResponseRedirect("/leaderboard")

@authorized
def player_leaderboard(request):
    try:
        tournament = get_tournament(request)

        tournament_players = PlayerTournamentScore.objects.filter(tournament=tournament).order_by("-score").all()
        player_game_counts = GamePlayer.objects.filter(game__tournament=tournament).values("player__id").annotate(gcount=Count("player__id"))
        game_counts_map = defaultdict(int)
        for result in player_game_counts:
            game_counts_map[result["player__id"]] = result["gcount"]

        positions = ("top", "jungle", "mid", "bot", "support")

        csv = "\\n".join(
            ",".join([
                str(tp.player.team.short_name),
                str(tp.player.in_game_name),
                str(tp.player.position),
                str(game_counts_map[tp.player.id]),
                str(tp.score)
            ]) for tp in tournament_players 
        )

        return render(request, "player_page.html", {
            "players": tournament_players,
            "positions": positions,
            "csv": csv,
            "with_cost": False
        })
    except Exception as e:
        print(e)
        

GRAPH_DATA_POINTS = 20
BUDGET = 90_000

@authorized
def draft(request):
    tournament = get_tournament(request)

    players = PlayerTournamentScore.objects.filter(tournament=tournament).order_by("-score").all()
    try:
        draft = UserDraft.objects.get(user=request.user)
    except:
        draft = UserDraft(user=request.user, score=0)
        draft.save()

    positions = ("top", "jungle", "mid", "bot", "support")

    position_players = {}
    player_costs = {}

    for player in players:
        player_costs[player.player.id] = player.cost

    players = sorted(players, key=lambda p: p.cost, reverse=True)

    for draft_player in UserDraftPlayer.objects.filter(draft=draft):
        if draft_player.player.id in player_costs:
            position_players[draft_player.player.position] = draft_player.player.id

    for pos in positions:
        if pos not in position_players:
            position_players[pos] = "none"

    return render(request, "draft_page.html", {
        "players": players,
        "player_costs": player_costs,
        "positions": positions,
        "draft": position_players,
        "error": request.GET.get("error", ""),
        "tournament": tournament,
        "budget": BUDGET,
        "with_cost": True
    })

@authorized
def submit_draft(request):
    tournament = get_tournament(request, is_post=True)

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
        return HttpResponseRedirect(f"/draft?error=player&t={tournament.id}")

    players = PlayerTournamentScore.objects.filter(tournament=tournament, player__id__in=player_ids).all()

    score = 0
    cost = 0
    for player in players:
        score += player.score
        cost += player.cost

    if cost > BUDGET:
        return HttpResponseRedirect(f"/draft?error=cost&t={tournament.id}")

    try:
        user_draft = UserDraft.objects.get(user=request.user)
        user_draft.score = score
        user_draft.save()
    except:
        user_draft = UserDraft(user=request.user, score=score)
        user_draft.save()
    
    UserDraftPlayer.objects.filter(draft=user_draft).delete()

    for player in players:
        UserDraftPlayer(draft=user_draft, player=player.player).save()

    return HttpResponseRedirect("/draft")

@authorized
def player_graph(request, player_id=None):
    tournament = get_tournament(request)

    try:
        player = Player.objects.get(id=player_id)
    except:
        return HttpResponseBadRequest()
    
    game_scores = get_player_score_sources_per_game_for_tournament(player, tournament)
    game_names = [
        (game.team_a.short_name, game.team_a.id == game.winner,
         game.team_b.short_name, game.team_b.id == game.winner, game.id) for game, _ in game_scores
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

    player_score = PlayerTournamentScore.objects.filter(player=player, tournament=tournament).first()
    
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
        "player_score": player_score.score if player_score else 0,
        "graph_data": graph_data,
        "sources": sources,
        "scores": scores,
        "game_names": game_names,
        "source_totals": source_totals,
        "colspan": len(game_names) + 1
    })


POSITION_ORDER = ["top", "jungle", "mid", "bot", "support"]

@authorized
def game_page(request, game_id=None):
    game = Game.objects.filter(id=game_id).first()
    if not game:
        return HttpResponseNotFound()
    
    game_players = GamePlayer.objects.filter(game=game)
    player_stats = PlayerStat.objects.filter(game=game)
    scores = defaultdict(dict)
    team_players = {
        game.team_a.id: [],
        game.team_b.id: []
    }

    game_player_map = {}
    for game_player in game_players:
        game_player_map[game_player.player.id] = game_player
        team_players[game_player.team.id].append(game_player)
    
    sort_key = lambda gp: (POSITION_ORDER.index(gp.position), gp.player.in_game_name)
    players = sorted(team_players[game.team_a.id], key=sort_key) + sorted(team_players[game.team_b.id], key=sort_key)

    for stat in player_stats:
        scores[stat.player.id][stat.stat_name] = stat.stat_value

    stat_sources = set([stat.stat_name for stat in player_stats])
    stat_sources = list(sorted(stat_sources))
    stat_sources = [(source, source.replace("_", " ").title()) for source in stat_sources]
    
    return render(request, "game_page.html", {
        "game": game,
        "players": players,
        "sources": stat_sources,
        "scores": scores
    })


POSITION_COLOURS = {
    "top": ["#de3333", "#ff4444"],
    "jungle": ["#33de33", "#55ff55"],
    "mid": ["#3333de", "#5555ff"],
    "bot": ["#2299de", "#33aaff"],
    "support": ["#de0055", "#ff2277"]
}

@authorized
def stats_page(request, stat_source=None):
    tournament = get_tournament(request)

    stat_source = stat_source.lower()
    if stat_source != "total" and stat_source not in ALL_STAT_SOURCES:
        return HttpResponseNotFound()
    
    stat_by_role = defaultdict(list)

    for tournament_player in PlayerTournamentScore.objects.filter(tournament=tournament).all():
        for _, score in get_player_score_sources_per_game_for_tournament(tournament_player.player, tournament):
            if stat_source == "total":
                stat_value = score.score
            else:
                stat_value = score.get(stat_source)
            stat_by_role[tournament_player.player.position].append(stat_value)

    stat_name = stat_source.replace("_", " ").title()

    graph_data = {
        "labels": [stat_name],
        "datasets": [
            {
                "label": pos.title(),
                "backgroundColor": POSITION_COLOURS[pos][1],
                "borderColor": POSITION_COLOURS[pos][0],
                "borderWidth": 1,
                "outlierColor": "#999999",
                "padding": 10,
                "itemRadius": 0,
                "data": [stat_by_role[pos]]
            } for pos in POSITION_ORDER
        ]
    }

    return render(request, "stat_page.html", {
        "stat_name": stat_name,
        "graph_data": graph_data
    })
