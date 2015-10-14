from google.appengine.ext import db
from player import Player

class Game(db.Model):
  opponent = db.StringProperty(required=True)
  date = db.DateProperty(required=True, auto_now_add=True)
  venue = db.StringProperty(required=True)
  players = db.ListProperty(db.Key)
