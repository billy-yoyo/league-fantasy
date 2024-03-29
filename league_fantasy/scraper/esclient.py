

from django.conf import settings
from mwclient import Site
import json
from .cargo_client import CargoClient

# Copyright (c) 2018-2021 Megan Cutrofello 
# Part of this is copied from https://github.com/RheingoldRiver/mwcleric/blob/master/mwcleric/clients/session_manager.py
# We're recreating the lol client because installing mwrogue wasn't working on ubuntu inside a venv for some reason

class AuthCredentials(object):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

class SessionManager(object):
    """Manages instances of WikiClient
    """
    existing_wikis = {}

    def get_client(self, url = None, path = None, scheme=None,
                   credentials = None, force_new=False,
                   max_retries = 10,
                   **kwargs):
        if url in self.existing_wikis and not force_new:
            return self.existing_wikis[url]['client']
        if scheme is not None:
            client = Site(url, path=path, scheme=scheme, max_retries=max_retries, **kwargs)
        else:
            client = Site(url, path=path, max_retries=max_retries, **kwargs)
        if credentials:
            client.login(username=credentials.username, password=credentials.password)
        self.existing_wikis[url] = {'client': client}
        return client

class LolClient:
    def __init__(self, credentials):
        self.credentials = credentials
        self.client = session_manager.get_client(
          url="lol.fandom.com",
          path="/",
          scheme="https",
          max_retries=0,
          credentials=credentials
        )
        self.cargo_client = CargoClient(self.client)

    def get_player_data(self, player_names):
        player_query = ", ".join(f"'{player_name}'" for player_name in player_names)
        result = self.cargo_client.query(
            tables="Players=P",
            fields="P.ID, P.Player",
            where=f"P.Player in ({player_query})"
        )
        return result

    def get_team_data(self, tournament_official_name, teams):
        teams_query = ", ".join(f"'{team}'" for team in teams)
        result = self.cargo_client.query(
            tables="Teams=TM, TournamentRosters=TR",
            join_on="TM.OverviewPage=TR.Team",
            fields="TM.OverviewPage, TM.Name, TM.Short, TR.RosterLinks, TR.Roles",
            where=f"TM.OverviewPage IN ({teams_query}) AND TR.Tournament='{tournament_official_name}'"
        )
        return result

    def get_match_history(self, season_name, tournament_name):
        result = self.cargo_client.query(
          tables="ScoreboardGames=SG, Tournaments=T",
          join_on="SG.OverviewPage=T.OverviewPage",
          fields="T.Name, SG.DateTime_UTC, SG.Team1, SG.Team2, SG.RiotPlatformGameId, SG.Winner, SG.DateTime_UTC",
          where=f"T.OverviewPage = 'LEC/{season_name}/{tournament_name}'"
        )
        return result

    def get_data_and_timeline(self, rpgid, version = 5):
        """
        Queries Leaguepedia to return two jsons: The data & timeline from a single game.

        This function is limited in scope: It will not allow you to query multiple games in a single query;
        however, the MediaWiki API does support this. It also will not allow you to drop one of the jsons
        for a smaller response package if you don't require all of the data. You also must know the ID in advance.
        You can find IDs by querying the MatchScheduleGame Cargo table and looking up the RiotPlatformGameId field.

        Raises a KeyError in the case that data is not found.
        If Timeline is not found, `None` will be returned for that json (this happens for chronobreaks).

        This function is unavailable on wikis other than Leaguepedia.

        :param rpgid: A single riot_platform_game_id
        :param version: The API version of the json to download. Defaults to 4.
        :return: Two jsons, the data & timeline for the game
        """
        titles = f"V{version} data:{rpgid}|V{version} data:{rpgid}/Timeline"
        result = self.client.post(
            'query', prop='revisions', titles=titles, rvprop='content',
            rvslots='main'
        )
        data = None
        timeline = None
        for _, page_data in result['query']['pages'].items():
            # This is lazy but there's 2 pages total so it's safe tbh
            if 'Timeline' in page_data['title']:
                timeline = json.loads(page_data['revisions'][0]['slots']['main']['*'])
            else:
                data = json.loads(page_data['revisions'][0]['slots']['main']['*'])

        if data is None:
            raise KeyError
        return data, timeline

session_manager = SessionManager()
credentials = AuthCredentials(username=settings.BOT_USERNAME, password=settings.BOT_PASSWORD)
esclient = LolClient(credentials)


