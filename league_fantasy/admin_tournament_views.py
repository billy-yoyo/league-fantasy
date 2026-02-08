"""
Admin views for tournament creation and management.
"""
import re
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import Season, Tournament, Team, Player, PlayerTournamentScore, Game
from .scraper.esclient import esclient
import json


def parse_fandom_url(url):
    """
    Parse a Fandom URL to extract season name and tournament name.
    Example: https://lol.fandom.com/wiki/LEC/2026_Season/Spring_Season
    Returns: (disambig_name, season_name, tournament_name)
    """
    # Remove trailing slash if present
    url = url.rstrip('/')

    # Extract the wiki path part
    # Format: https://lol.fandom.com/wiki/REGION/SEASON/TOURNAMENT
    match = re.search(r'lol\.fandom\.com/wiki/(.+)', url)
    if not match:
        return None, None, None

    wiki_path = match.group(1)
    parts = wiki_path.split('/')

    if len(parts) < 2:
        return None, None, None

    # The full path is the disambig_name for Leaguepedia
    disambig_name = wiki_path

    # Try to extract season and tournament
    if len(parts) >= 3:
        # Format: REGION/SEASON/TOURNAMENT
        season_name = parts[1].replace('_', ' ')
        tournament_name = parts[2].replace('_', ' ')
    elif len(parts) == 2:
        # Format: REGION/TOURNAMENT (no explicit season)
        season_name = parts[0].replace('_', ' ')
        tournament_name = parts[1].replace('_', ' ')
    else:
        season_name = parts[0].replace('_', ' ')
        tournament_name = parts[0].replace('_', ' ')

    return disambig_name, season_name, tournament_name


@staff_member_required
@require_http_methods(["GET", "POST"])
def tournament_setup_start(request):
    """
    Step 1: Enter Fandom URL and fetch tournament information.
    """
    if request.method == "GET":
        print("rendering setup")
        try:
            return render(request, 'admin/tournament_setup_start.html')
        except Exception as e:
            print(f"Error: {e}")
            raise e
            
            
    # POST - Process the URL
    fandom_url = request.POST.get('fandom_url', '').strip()
    if not fandom_url:
        return render(request, 'admin/tournament_setup_start.html', {
            'error': 'Please provide a Fandom URL.'
        })

    # Parse the URL
    disambig_name, season_name, tournament_name = parse_fandom_url(fandom_url)

    if not disambig_name or not season_name or not tournament_name:
        return render(request, 'admin/tournament_setup_start.html', {
            'error': 'Could not parse the Fandom URL. Please check the format.'
        })

    # Store in session for next steps (this replaces any existing data)
    request.session['tournament_setup'] = {
        'fandom_url': fandom_url,
        'disambig_name': disambig_name,
        'season_name': season_name,
        'tournament_name': tournament_name,
    }
    request.session.modified = True

    print(f"Step 1 complete. Redirecting to teams page for: {tournament_name}")
    return redirect('admin_tournament_setup_teams')


@staff_member_required
@require_http_methods(["GET", "POST"])
def tournament_setup_teams(request):
    """
    Step 2: Scrape teams and display roster editor.
    """
    print(f"step 2 accessed, method is {request.method}")
    setup_data = request.session.get('tournament_setup')
    if not setup_data:
        return redirect('admin_tournament_setup_start')

    # Clear any existing teams data when arriving fresh from step 1
    if request.method == "GET" and 'teams' in setup_data:
        print("Clearing existing teams data from session")
        del setup_data['teams']
        request.session['tournament_setup'] = setup_data
        request.session.modified = True

    if request.method == "GET":
        # Scrape teams from Fandom
        try:
            client = esclient
            disambig_name = setup_data['disambig_name'].replace("_", " ")
            print(f"Step 2 (GET): Scraping teams for {disambig_name}")

            # Get team data from Leaguepedia
            team_data = client.get_team_data(disambig_name, [])
            print(f"Found {len(team_data) if team_data else 0} teams")

            if not team_data or len(team_data) == 0:
                return render(request, 'admin/tournament_setup_start.html', {
                    'error': f'No teams found for tournament: {disambig_name}. Please check the URL or verify it exists on Leaguepedia.'
                })

            # Process team data
            teams_info = []
            all_disambig_names = []  # Collect disambiguated names first

            # Debug: Print first team entry to see structure
            if team_data:
                print(f"Sample team entry keys: {list(team_data[0].keys())}")
                print(f"Sample team entry: {team_data[0]}")

            # First pass: collect all disambiguated player names
            for team_entry in team_data:
                roster_links = team_entry.get('RosterLinks', '')
                if roster_links:
                    players = roster_links.split(';;')
                    for player in players:
                        if player.strip():
                            all_disambig_names.append(player.strip())

            # Get actual in-game names from Leaguepedia
            print(f"Looking up {len(all_disambig_names)} player IGNs from disambiguated names")
            disambig_to_ign = {}  # Map disambiguated name -> in-game name
            if all_disambig_names:
                player_data_results = client.get_player_data(all_disambig_names)
                for player_data in player_data_results:
                    official_name = player_data.get('Player', '')  # Disambiguated name
                    in_game_name = player_data.get('ID', '')       # Actual IGN
                    if official_name and in_game_name:
                        disambig_to_ign[official_name] = in_game_name
                        print(f"  Mapped: {official_name} -> {in_game_name}")

            # Second pass: process teams with proper IGNs
            for team_entry in team_data:
                # Use 'Name' field instead of 'Team'
                team_name = team_entry.get('Name', '') or team_entry.get('Team', '')
                print(f"Processing team: '{team_name}' from entry with keys: {list(team_entry.keys())}")
                if not team_name:
                    print(f"  Skipping - no team name found")
                    continue

                # Parse roster from RosterLinks and Roles if available
                roster = {}
                roster_links = team_entry.get('RosterLinks', '')
                roles = team_entry.get('Roles', '')

                if roster_links and roles:
                    # Split by ;; to get individual players and roles
                    players = roster_links.split(';;')
                    positions = roles.split(';;')

                    # Map roles to our position names
                    role_mapping = {
                        'Top': 'top',
                        'Jungle': 'jungle',
                        'Mid': 'mid',
                        'Bot': 'bot',
                        'Support': 'support'
                    }

                    # Match players to positions, converting to IGNs
                    for player_disambig, role in zip(players, positions):
                        normalized_role = role_mapping.get(role, '')
                        if normalized_role and player_disambig.strip():
                            # Use the in-game name if we found it, otherwise use disambiguated name
                            ign = disambig_to_ign.get(player_disambig.strip(), player_disambig.strip())
                            roster[normalized_role] = ign

                # Fill in missing positions with empty strings
                for pos in ['top', 'jungle', 'mid', 'bot', 'support']:
                    if pos not in roster:
                        roster[pos] = ''

                team_info = {
                    'name': team_name,
                    'overview_page': team_entry.get('OverviewPage', ''),
                    'region': team_entry.get('Region', ''),
                    'roster': roster
                }
                teams_info.append(team_info)
                print(f"  Added team with roster: {roster}")

            # Check if we got any valid teams after processing
            print(f"Processed {len(teams_info)} teams from raw data")
            for i, team in enumerate(teams_info[:3]):  # Print first 3 teams for debugging
                print(f"  Team {i}: {team['name']} - Roster: {team['roster']}")

            if not teams_info or len(teams_info) == 0:
                return render(request, 'admin/tournament_setup_start.html', {
                    'error': f'No valid teams found for tournament: {disambig_name}. Please check the URL or verify the tournament exists on Leaguepedia.'
                })

            # Collect all in-game names from rosters
            all_igns = []
            for team in teams_info:
                for pos, ign in team['roster'].items():
                    if ign:
                        all_igns.append(ign)

            # Get existing players from database using IGNs
            existing_players = {}
            if all_igns:
                players = Player.objects.filter(in_game_name__in=all_igns)
                for player in players:
                    existing_players[player.in_game_name] = {
                        'id': player.id,
                        'team': player.team.full_name if player.team else '',
                        'country': player.country,
                    }

            # Store teams data in session
            setup_data['teams'] = teams_info
            request.session['tournament_setup'] = setup_data
            request.session.modified = True

            context = {
                'season_name': setup_data['season_name'],
                'tournament_name': setup_data['tournament_name'],
                'teams': teams_info,
                'teams_json': json.dumps(teams_info),
                'existing_players': json.dumps(existing_players),
            }

            print(f"Rendering teams page with {len(teams_info)} teams")
            return render(request, 'admin/tournament_setup_teams.html', context)

        except Exception as e:
            # Log the full error for debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in tournament_setup_teams: {error_details}")

            return render(request, 'admin/tournament_setup_start.html', {
                'error': f'Error fetching team data: {str(e)}'
            })

    # POST - Save roster data and move to cost generation
    try:
        teams_data = json.loads(request.POST.get('teams_data', '[]'))
        setup_data['teams'] = teams_data
        request.session['tournament_setup'] = setup_data
        request.session.modified = True

        return redirect('admin_tournament_setup_costs')
    except Exception as e:
        return HttpResponseBadRequest(f'Error processing team data: {str(e)}')


@staff_member_required
@require_http_methods(["GET", "POST"])
def tournament_setup_costs(request):
    """
    Step 3: Generate and edit player costs.
    """
    setup_data = request.session.get('tournament_setup')
    print(f"Step 3 accessed. Method: {request.method}, Has setup_data: {setup_data is not None}, Has teams: {'teams' in setup_data if setup_data else False}")

    if not setup_data or 'teams' not in setup_data:
        print("Redirecting back to start - missing setup data or teams")
        return redirect('admin_tournament_setup_start')

    if request.method == "GET":
        # Get list of all tournaments for cost calculation
        tournaments = Tournament.objects.select_related('season').order_by('-id')

        context = {
            'season_name': setup_data['season_name'],
            'tournament_name': setup_data['tournament_name'],
            'teams': json.dumps(setup_data['teams']),
            'tournaments': tournaments,
            'default_cps': 1500,
            'default_bc': 30000,
            'default_factor': 2,
            'default_power': 0.8,
            'default_rookie_cost': 10000,
        }

        return render(request, 'admin/tournament_setup_costs.html', context)

    # POST - Calculate costs or finalize
    action = request.POST.get('action')

    if action == 'calculate':
        # Calculate costs based on previous tournaments
        try:
            # Get parameters
            selected_tournaments = request.POST.getlist('previous_tournaments')
            cps = float(request.POST.get('cps', 1500))
            bc = float(request.POST.get('bc', 30000))
            factor = float(request.POST.get('factor', 2))
            power = float(request.POST.get('power', 0.8))
            rookie_cost = float(request.POST.get('rookie_cost', 10000))

            # Calculate costs for each player
            costs, player_details = calculate_player_costs(
                setup_data['teams'],
                selected_tournaments,
                cps, bc, factor, power, rookie_cost
            )

            # Store costs and details in session
            setup_data['costs'] = costs
            setup_data['player_details'] = player_details
            setup_data['cost_params'] = {
                'cps': cps,
                'bc': bc,
                'factor': factor,
                'power': power,
                'rookie_cost': rookie_cost,
                'previous_tournaments': selected_tournaments,
            }
            request.session['tournament_setup'] = setup_data
            request.session.modified = True

            # Return calculated costs and details as JSON
            return JsonResponse({
                'success': True,
                'costs': costs,
                'player_details': player_details
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    elif action == 'submit':
        # Save the tournament with final costs
        try:
            costs_data = json.loads(request.POST.get('costs_data', '{}'))
            setup_data['costs'] = costs_data
            request.session['tournament_setup'] = setup_data
            request.session.modified = True

            return redirect('admin_tournament_setup_submit')

        except Exception as e:
            return HttpResponseBadRequest(f'Error processing costs: {str(e)}')

    return HttpResponseBadRequest('Invalid action')


@staff_member_required
@require_http_methods(["POST"])
def tournament_setup_submit(request):
    """
    Step 4: Create the tournament, teams, players, and set costs.
    """
    setup_data = request.session.get('tournament_setup')
    if not setup_data or 'teams' not in setup_data or 'costs' not in setup_data:
        return redirect('admin_tournament_setup_start')

    try:
        with transaction.atomic():
            # Create or get season
            season, _ = Season.objects.get_or_create(
                name=setup_data['season_name']
            )

            # Create tournament
            tournament = Tournament.objects.create(
                name=setup_data['tournament_name'],
                season=season,
                disambig_name=setup_data['disambig_name'],
                active=False  # Admin can activate later
            )

            # Create teams and players
            for team_data in setup_data['teams']:
                # Get or create team
                team, _ = Team.objects.get_or_create(
                    full_name=team_data['name'],
                    defaults={
                        'short_name': team_data['name'][:10],
                        'overview_page': team_data.get('overview_page', ''),
                        'region': team_data.get('region', ''),
                        'active': True,
                    }
                )

                # Create or update players
                roster = team_data.get('roster', {})
                for position, player_data in roster.items():
                    if not player_data:
                        continue

                    # Handle both string (player name) and dict (player data) formats
                    if isinstance(player_data, str):
                        player_name = player_data
                        player_country = ''
                    else:
                        player_name = player_data.get('name', '')
                        player_country = player_data.get('country', '')

                    if not player_name:
                        continue

                    # Get or create player
                    player, created = Player.objects.get_or_create(
                        in_game_name=player_name,
                        defaults={
                            'team': team,
                            'position': position,
                            'country': player_country,
                            'active': True,
                        }
                    )

                    # Update player if exists but data changed
                    if not created:
                        player.team = team
                        player.position = position
                        if player_country:
                            player.country = player_country
                        player.save()

                    # Create PlayerTournamentScore with calculated cost
                    cost = setup_data['costs'].get(player_name, 10000)
                    PlayerTournamentScore.objects.create(
                        player=player,
                        tournament=tournament,
                        score=0,
                        cost=cost
                    )

            # Clear session data
            del request.session['tournament_setup']
            request.session.modified = True

            # Redirect to tournament admin page
            return redirect(f'/admin/league_fantasy/tournament/{tournament.id}/change/')

    except Exception as e:
        return HttpResponseBadRequest(f'Error creating tournament: {str(e)}')


def calculate_player_costs(teams, tournament_ids, cps, bc, factor, power, rookie_cost):
    """
    Calculate costs for all players based on previous tournament performance.

    Formula: (max(min((S * T * CpS) / Bc, F), 0) ** P) * Bc
    Where:
        S = average score per game
        T = number of tournaments played
        CpS = cost per score
        Bc = base cost
        F = factor (threshold)
        P = power

    Returns: (costs_dict, player_details_dict)
        costs_dict: {player_name: cost}
        player_details_dict: {player_name: {
            'tournaments': {tournament_id: {'score_per_game': float, 'games': int}},
            'avg_score_per_game': float,
            'tournament_count': int
        }}
    """
    costs = {}
    player_details = {}

    # Get all player names from teams
    player_names = set()
    for team in teams:
        roster = team.get('roster', {})
        for position, player_data in roster.items():
            if isinstance(player_data, str):
                player_name = player_data
            else:
                player_name = player_data.get('name', '') if player_data else ''

            if player_name:
                player_names.add(player_name)

    print(f"checking tournament ids {tournament_ids}")
    # Get previous tournament scores for each player
    for player_name in player_names:
        try:
            player = Player.objects.filter(in_game_name__iexact=player_name).first()
        except Player.DoesNotExist:
            print(f"player does not exist: {player_name}")
            # New player - assign rookie cost
            costs[player_name] = rookie_cost
            player_details[player_name] = {
                'tournaments': {},
                'avg_score_per_game': 0,
                'tournament_count': 0,
                'is_rookie': True
            }
            continue

        # Get scores from previous tournaments
        tournament_scores = PlayerTournamentScore.objects.filter(
            player=player,
            tournament_id__in=tournament_ids
        ).select_related('tournament')

        if not tournament_scores.exists():
            print(f"player is not in any tournaments: {player_name}")
            # Rookie - no previous tournament data
            costs[player_name] = rookie_cost
            player_details[player_name] = {
                'tournaments': {},
                'avg_score_per_game': 0,
                'tournament_count': 0,
                'is_rookie': True
            }
            continue

        # Calculate average score per game
        total_score_per_game = 0
        tournament_count = 0
        tournament_data = {}

        for pts in tournament_scores:
            # Get games played in this tournament
            games_played = Game.objects.filter(
                tournament=pts.tournament,
                gameplayer__player=player
            ).distinct().count()

            if games_played > 0:
                score_per_game = pts.score / games_played
                total_score_per_game += score_per_game
                tournament_count += 1

                tournament_data[pts.tournament.id] = {
                    'score_per_game': round(score_per_game, 2),
                    'games': games_played,
                    'total_score': pts.score
                }

        if tournament_count == 0:
            print(f"player had no scores for any tournaments: {player_name}")
            costs[player_name] = rookie_cost
            player_details[player_name] = {
                'tournaments': {},
                'avg_score_per_game': 0,
                'tournament_count': 0,
                'is_rookie': True
            }
            continue

        # Calculate average score per game across all tournaments
        avg_score_per_game = total_score_per_game / tournament_count

        # Apply the formula
        # (max(min((S * T * CpS) / Bc, F), 0) ** P) * Bc
        S = avg_score_per_game
        T = tournament_count

        inner = (S * T * cps) / bc
        clamped = max(min(inner, factor), 0)
        cost = (clamped ** power) * bc

        costs[player_name] = round(cost)
        player_details[player_name] = {
            'tournaments': tournament_data,
            'avg_score_per_game': round(avg_score_per_game, 2),
            'tournament_count': tournament_count,
            'is_rookie': False
        }

    return costs, player_details
