import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandParser
from PIL import Image
from io import BytesIO
from ...models import PlayerTournamentScore, Player
import os
import urllib

PLAYER_IMAGES = os.path.join(os.path.dirname(__file__), "..", "..", "static", "players")

def get_player_image_url(player_name):
  quoted_name = urllib.parse.quote(player_name.replace(" ", "_"))

  resp = requests.get(f"https://lol.fandom.com/wiki/{quoted_name}")
  html = resp.text
  soup = BeautifulSoup(html, "lxml")
  image = soup.select_one("#infoboxPlayer .image img")
  return image.get("src")

def download_player_image(player_id, image_url):
  if not os.path.exists(PLAYER_IMAGES):
    os.mkdir(PLAYER_IMAGES)
  
  resp = requests.get(image_url)
  image = Image.open(BytesIO(resp.content))
  image.save(os.path.join(PLAYER_IMAGES, f"{player_id}.png"))

class Command(BaseCommand):
  help = "Get Player Images"
  
  def add_arguments(self, parser: CommandParser) -> None:
    parser.add_argument("--player", type=str, required=False)
    parser.add_argument("--tournament", type=int, required=False)

  def handle(self, *args, **options):
    if options.get("player", None) is not None:
      player_name = options["player"]
      player = Player.objects.filter(in_game_name__iexact=player_name).first()
      if not player:
        raise Exception(f"invalid player name {player_name}")

      players = [(player.id, player.overview_page)]
    elif options.get("tournament", None) is not None:
      players = []
      for row in PlayerTournamentScore.objects.filter(tournament__id=options["tournament"]).all():
        players.append((row.player.id, row.player.overview_page))
    else:
      raise Exception("must specify either player or tournament")

    for player_id, player_name in players:
      try:
        image_url = get_player_image_url(player_name)
        download_player_image(player_id, image_url)
        print(f"+ downloaded image for player {player_id}: {player_name}")
      except Exception as e:
        print(f"- failed to download image for player {player_id}: {player_name}")
        print(e)



