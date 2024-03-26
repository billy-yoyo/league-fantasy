from django.db import models
from django.conf import settings

class Season(models.Model):
  name = models.CharField(max_length=255)

  def __str__(self):
    return self.name

class Tournament(models.Model):
  name = models.CharField(max_length=255)
  season = models.ForeignKey(Season, on_delete=models.CASCADE)

  def __str__(self):
    return self.name

class Team(models.Model):
  full_name = models.CharField(max_length=70)
  short_name = models.CharField(max_length=10)
  team_id = models.CharField(max_length=70)
  icon_url = models.CharField(max_length=255)
  active = models.BooleanField(default=True)

  def __str__(self) -> str:
    return self.full_name
  
class Game(models.Model):
  game_id = models.CharField(max_length=70)
  team_a = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_a")
  team_b = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_b")
  winner = models.CharField(max_length=70)
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

  def __str__(self):
    return self.game_id

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
  active = models.BooleanField(default=True)

  def __str__(self):
    return self.in_game_name

class PlayerSynonym(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  name = models.CharField(max_length=70)

  def __str__(self):
    return self.name

class PlayerScorePoint(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  score = models.FloatField()
  time = models.DateTimeField()

class PlayerStat(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  game = models.ForeignKey(Game, on_delete=models.CASCADE)
  stat_name = models.CharField(max_length=70)
  stat_value = models.FloatField()

  def __str__(self):
    return self.stat_name

class UserDraft(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  score = models.FloatField()

class UserDraftScorePoint(models.Model):
  draft = models.ForeignKey(UserDraft, on_delete=models.CASCADE)
  score = models.FloatField()
  time = models.DateTimeField()

class UserDraftPlayer(models.Model):
  draft = models.ForeignKey(UserDraft, on_delete=models.CASCADE)
  player = models.ForeignKey(Player, on_delete=models.CASCADE)


