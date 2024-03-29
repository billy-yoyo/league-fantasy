from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
from django.conf import settings

credentials = AuthCredentials(username=settings.BOT_USERNAME, password=settings.BOT_PASSWORD)
esclient = EsportsClient("lol", credentials=credentials)
