from django.db import models

class Tournament(models.Model):
  name = models.CharField(max_length=255)

class Team(models.Model):
  full_name = models.CharField(max_length=70)
  short_name = models.CharField(max_length=10)
  team_id = models.CharField(max_length=70)
  icon_url = models.CharField(max_length=255)

  def __str__(self) -> str:
    return self.full_name
  
class Game(models.Model):
  game_id = models.CharField(max_length=70)
  team_a = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_a")
  team_b = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_b")
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

class Player(models.Model):
  POSITIONS = {
    "top": "Top",
    "jungle": "Jungle",
    "mid": "Mid",
    "bot": "Bot",
    "support": "Support"
  }
  in_game_name = models.CharField(max_length=70)
  team = models.ForeignKey(Team, on_delete=models.CASCADE)
  player_id = models.CharField(max_length=70)
  country = models.CharField(max_length=5)
  position = models.CharField(max_length=70, choices=POSITIONS)
  score = models.FloatField()


class PlayerStat(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  game = models.ForeignKey(Game, on_delete=models.CASCADE)
  stat_name = models.CharField(max_length=70)
  stat_value = models.FloatField()


