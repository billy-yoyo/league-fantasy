import json
import os

with open(os.path.join(os.path.dirname(__file__), "./champions.json"), encoding="utf-8") as f:
  champions = json.load(f)

def get_champion_icon_and_name(champion_id):
  for champion in champions:
    if champion["key"] == str(champion_id):
      return champion["icon"], champion["name"]
  return None, None