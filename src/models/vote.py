from google.appengine.ext import db
from player import Player
from game import Game

class Vote(db.Model):
  game = db.ReferenceProperty(Game, required=True)
  voter = db.ReferenceProperty(Player, collection_name="voter")
  three = db.ReferenceProperty(Player, collection_name="three_votes")
  two = db.ReferenceProperty(Player, collection_name="two_votes")
  one = db.ReferenceProperty(Player, collection_name="one_votes")

class PlayerGameVotes(db.Model):
  game = db.ReferenceProperty(Game, required=True)
  player = db.ReferenceProperty(Player, required=True)
  threes = db.IntegerProperty(default=0)
  twos = db.IntegerProperty(default=0)
  ones = db.IntegerProperty(default=0)

  def ranking_points(self):
    # Ranking is by total votes, then number of threes, then number of twos
    return 3 * self.threes + 2 * self.twos + self.ones \
           + self.threes / 1000.0 + self.twos / 1000000.0

class PlayerOverallVotes(db.Model):
  player = db.ReferenceProperty(Player, required=True)
  threes = db.IntegerProperty(default=0)
  twos = db.IntegerProperty(default=0)
  ones = db.IntegerProperty(default=0)

  def ranking_points(self):
    # Ranking is by total votes, then number of threes, then number of twos
    return 3 * self.threes + 2 * self.twos + self.ones \
           + self.threes / 1000.0 + self.twos / 1000000.0

class SelfVote(db.Model):
  game = db.ReferenceProperty(Game, required=True)
  voter = db.ReferenceProperty(Player)
