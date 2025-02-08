from collections import defaultdict

class ScoreComputer:
  def __init__(self, score, multiplier=1):
    self.score = score
    self.score_sources = defaultdict(int)
    self.multiplier = multiplier
  
  def get(self, source):
    return self.score_sources.get(source, 0)

  def add(self, name, value):
    self.score += value * self.multiplier
    self.score_sources[name] += value * self.multiplier

  def merge(self, score):
    self.score += score.score
    for name, value in score.score_sources.items():
      self.score_sources[name] += value

  def summary(self, name):
    lines = [f"Score for {name} was {self.score}:"]
    for name, value in sorted(self.score_sources.items()):
      lines.append(f"    {name}: {value}")
    return "\n".join(lines)
  
  def __contains__(self, item):
    return item in self.score_sources
