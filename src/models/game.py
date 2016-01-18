from google.appengine.ext import ndb
from player import Player

class Team:
  MEN = 1
  WOMEN = 2
  TEST = -1

  @staticmethod
  def getAll():
    return ["Men", "Women", "Test"]

  @staticmethod
  def getString(team):
    if team == Team.MEN:
      return "Men"
    elif team == Team.WOMEN:
      return "Women"
    elif team == Team.TEST:
      return "Test"
    else:
      return None

  @staticmethod
  def getTeam(team_string):
    if team_string.lower().strip() == "men":
      return Team.MEN
    elif team_string.lower().strip() == "women":
      return Team.WOMEN
    elif team_string.lower().strip() == "test":
      return Team.TEST
    else:
      return None

class Game(ndb.Model):
  opponent = ndb.StringProperty(required=True)
  date = ndb.DateProperty(required=True, auto_now_add=True)
  venue = ndb.StringProperty(required=True)
  team = ndb.IntegerProperty(required=True)
  players = ndb.KeyProperty(kind=Player, repeated=True)
  weight = ndb.FloatProperty(required=True, default=1.0)

class GameResults(ndb.Model):
  game = ndb.KeyProperty(kind=Game, required=True)
  three = ndb.KeyProperty(kind=Player)
  two = ndb.KeyProperty(kind=Player)
  one = ndb.KeyProperty(kind=Player)
  voters = ndb.IntegerProperty(default=0)
