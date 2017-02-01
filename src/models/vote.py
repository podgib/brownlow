from google.appengine.ext import ndb
from player import Player
from game import Game

class Vote(ndb.Model):
  game = ndb.KeyProperty(kind=Game, required=True)
  voter = ndb.KeyProperty(kind=Player)
  three = ndb.KeyProperty(kind=Player)
  two = ndb.KeyProperty(kind=Player)
  one = ndb.KeyProperty(kind=Player)

class PlayerGameVotes(ndb.Model):
  game = ndb.KeyProperty(kind=Game, required=True)
  player = ndb.KeyProperty(kind=Player, required=True)
  threes = ndb.IntegerProperty(default=0)
  twos = ndb.IntegerProperty(default=0)
  ones = ndb.IntegerProperty(default=0)

  def ranking_points(self):
    # Ranking is by total votes, then number of threes, then number of twos
    return 3 * self.threes + 2 * self.twos + self.ones \
           + self.threes / 1000.0 + self.twos / 1000000.0

  def total(self):
    return 3 * self.threes + 2 * self.twos + self.ones

class PlayerOverallVotes(ndb.Model):
  player = ndb.KeyProperty(kind=Player, required=True)
  threes = ndb.IntegerProperty(default=0)
  twos = ndb.IntegerProperty(default=0)
  ones = ndb.IntegerProperty(default=0)
  total = ndb.FloatProperty(default=0)

  def ranking_points(self):
    # Ranking is by total votes, then number of threes, then number of twos
    return self.total + self.threes / 1000.0 + self.twos / 1000000.0

class SelfVote(ndb.Model):
  game = ndb.KeyProperty(kind=Game, required=True)
  voter = ndb.KeyProperty(kind=Player)
