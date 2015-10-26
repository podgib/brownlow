from google.appengine.ext import db
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

class Game(db.Model):
  opponent = db.StringProperty(required=True)
  date = db.DateProperty(required=True, auto_now_add=True)
  venue = db.StringProperty(required=True)
  team = db.IntegerProperty(required=True)
  players = db.ListProperty(db.Key)

class GameResults(db.Model):
  game = db.ReferenceProperty(Game, required=True)
  three = db.ReferenceProperty(Player, collection_name="three_game_votes")
  two = db.ReferenceProperty(Player, collection_name="two_game_votes")
  one = db.ReferenceProperty(Player, collection_name="one_game_votes")
