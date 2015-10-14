from google.appengine.ext import db

from player import Player
from game import Game

class Token(db.Model):
  value = db.StringProperty(required=True)
  voter = db.ReferenceProperty(Player, required=True)
  game = db.ReferenceProperty(Game, required=True)
  used = db.BooleanProperty(default=False, required=True)