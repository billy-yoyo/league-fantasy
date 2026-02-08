# Admin Tournament Setup Guide

This guide explains how to use the new admin tournament creation feature.

## Overview

The admin tournament setup is a 3-step wizard that allows staff members to:
1. Enter a Leaguepedia (Fandom) URL and automatically extract tournament information
2. Review and edit team rosters scraped from Leaguepedia
3. Generate and adjust player costs based on previous tournament performance

## Access

The tournament setup wizard is available at: `/admin/tournament-setup/`

**Requirements:** You must be logged in as a staff member (Django admin user).

## Step 1: Enter Tournament Information

1. Navigate to `/admin/tournament-setup/`
2. Enter the full Leaguepedia URL for the tournament
   - Example: `https://lol.fandom.com/wiki/LEC/2026_Season/Spring_Season`
3. Click "Continue to Team Setup"

The system will automatically:
- Extract the season name (e.g., "2026 Season")
- Extract the tournament name (e.g., "Spring Season")
- Generate the disambig_name for Leaguepedia queries (e.g., "LEC/2026_Season/Spring_Season")

## Step 2: Configure Team Rosters

The system will automatically scrape Leaguepedia to fetch:
- All teams in the tournament
- Player names for each position (top, jungle, mid, bot, support)
- Team regions and overview pages

You can:
- Review the scraped roster information
- Edit player names if needed
- Add country codes for players
- Add missing players that weren't scraped

Existing players in the database will have their country codes pre-filled automatically.

Click "Continue to Cost Generation" when done.

## Step 3: Generate and Adjust Player Costs

### Cost Calculation Parameters

Select previous tournaments to base costs on (hold Ctrl/Cmd to select multiple), then configure:

1. **Cost per Score (CpS)** - Default: 1500
   - How much to multiply player score/game by

2. **Base Cost (Bc)** - Default: 30,000
   - The base cost to help scale the costs by

3. **Factor (F)** - Default: 2
   - The threshold factor to cap the scores by

4. **Power (P)** - Default: 0.8
   - The power to raise the scores by

5. **Rookie Cost** - Default: 10,000
   - Cost assigned to players with no previous tournament data

### Cost Calculation Formula

For players with previous tournament data:
```
(max(min((S * T * CpS) / Bc, F), 0) ** P) * Bc
```

Where:
- **S** = Average score per game across selected tournaments
- **T** = Number of tournaments the player participated in

### Process

1. Select previous tournaments from the list (hold Ctrl/Cmd for multiple)
2. Adjust parameters if needed (defaults usually work well)
3. Click "Calculate Costs" to generate costs
4. Review the calculated costs in the table
5. Manually adjust any costs as needed
6. Click "Create Tournament" to finalize

## What Gets Created

When you click "Create Tournament", the system will:

1. **Create or get the Season** with the extracted name
2. **Create the Tournament** with:
   - Name from URL
   - Season reference
   - Disambig name for Leaguepedia
   - Active = False (you can activate it later in admin)
3. **Create or update Teams** with:
   - Full name, short name
   - Overview page from Leaguepedia
   - Region
4. **Create or update Players** with:
   - In-game name
   - Team assignment
   - Position
   - Country code
5. **Create PlayerTournamentScore entries** with:
   - Initial score = 0
   - Cost from calculation or manual adjustment

## After Creation

After the tournament is created, you'll be redirected to the Django admin page for the tournament where you can:
- Activate the tournament
- Run additional scraping actions (match list, team data updates)
- Recalculate scores
- Make other adjustments

## Technical Details

### Files Created/Modified

- `league_fantasy/admin_tournament_views.py` - View logic for 3-step wizard
- `league_fantasy/urls.py` - URL patterns for wizard steps
- `templates/admin/tournament_setup_start.html` - Step 1 template
- `templates/admin/tournament_setup_teams.html` - Step 2 template
- `templates/admin/tournament_setup_costs.html` - Step 3 template

### Key Functions

- `parse_fandom_url()` - Extracts season/tournament from URL
- `calculate_player_costs()` - Implements cost calculation formula
- Session storage used to pass data between wizard steps

### Dependencies

- Uses existing `LolClient` from `league_fantasy.scraper.esclient`
- Integrates with existing models: Season, Tournament, Team, Player, PlayerTournamentScore
- Requires Leaguepedia bot credentials configured in settings
