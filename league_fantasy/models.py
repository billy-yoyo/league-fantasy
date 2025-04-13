from django.db import models
from django.conf import settings

class Season(models.Model):
  name = models.CharField(max_length=255)

  def __str__(self):
    return self.name

class Tournament(models.Model):
  name = models.CharField(max_length=255)
  season = models.ForeignKey(Season, on_delete=models.CASCADE)
  active = models.BooleanField(default=False)
  disambig_name = models.CharField(max_length=255)

  def __str__(self):
    return self.name

class Team(models.Model):
  full_name = models.CharField(max_length=70)
  short_name = models.CharField(max_length=10)
  overview_page = models.CharField(max_length=255, default="")
  icon_url = models.CharField(max_length=255, default="")
  background_colour = models.CharField(max_length=10, default="#ffffff")
  active = models.BooleanField(default=True)
  region = models.CharField(max_length=255)

  def __str__(self) -> str:
    return self.full_name
  
class Game(models.Model):
  team_a = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_a")
  team_b = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_b")
  winner = models.IntegerField()
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
  time = models.DateTimeField()
  rpgid = models.CharField(max_length=70)
  statistics_loaded = models.BooleanField(default=False)
  game_duration = models.FloatField(default=1)
  match_id = models.CharField(max_length=255, default="")

  def __str__(self):
    return self.rpgid


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
  country = models.CharField(max_length=70, default="none")
  position = models.CharField(max_length=70, choices=POSITIONS)
  score = models.FloatField(default=0)
  active = models.BooleanField(default=True)
  overview_page = models.CharField(max_length=255, default=0)

  def __str__(self):
    return self.in_game_name

class PlayerTournamentScore(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
  score = models.FloatField(default=0)
  cost = models.FloatField(default=0)

class GamePlayer(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  position = models.CharField(max_length=70, choices=Player.POSITIONS)
  team = models.ForeignKey(Team, on_delete=models.CASCADE)
  game = models.ForeignKey(Game, on_delete=models.CASCADE)

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
  score_offset = models.FloatField(default=0)
  colour = models.CharField(max_length=10, default="#000000")

  def __str__(self):
    return self.user.username

class UserDraftScorePoint(models.Model):
  draft = models.ForeignKey(UserDraft, on_delete=models.CASCADE)
  score = models.FloatField()
  time = models.DateTimeField()

class UserDraftPlayer(models.Model):
  draft = models.ForeignKey(UserDraft, on_delete=models.CASCADE)
  player = models.ForeignKey(Player, on_delete=models.CASCADE)

class Leaderboard(models.Model):
  name = models.CharField(max_length=70)

  def __str__(self):
    return self.name

class LeaderboardMember(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE)
  is_admin = models.BooleanField()

  def __str__(self):
    return self.user.username
  
class Champion(models.Model):
  champion_id = models.IntegerField(primary_key=True)
  champion_name = models.CharField(max_length=255)

  def __str__(self):
    return self.champion_name

class TournamentChampion(models.Model):
  champion = models.ForeignKey(Champion, on_delete=models.CASCADE)
  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
  score = models.FloatField(default=0)
  games = models.IntegerField(default=0)
