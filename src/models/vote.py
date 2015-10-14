from google.appengine.ext import db
from player import Player
from game import Game

class Vote(db.Model):
  game = db.ReferenceProperty(Game, required=True)
  voter = db.ReferenceProperty(Player, collection_name="voter")
  three = db.ReferenceProperty(Player, collection_name="three")
  two = db.ReferenceProperty(Player, collection_name="two")
  one = db.ReferenceProperty(Player, collection_name="one")
