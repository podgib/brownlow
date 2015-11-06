from google.appengine.ext import ndb

from player import Player
from game import Game

class Token(ndb.Model):
  value = ndb.StringProperty(required=True)
  voter = ndb.KeyProperty(kind=Player, required=True)
  game = ndb.KeyProperty(kind=Game, required=True)
  used = ndb.BooleanProperty(default=False, required=True)