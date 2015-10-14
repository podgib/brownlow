import base64
import webapp2
import os
import jinja2
import logging
import datetime

from models.player import Player
from models.game import Game
from models.token import Token

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class AddPlayerHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/add_player.html")
    self.response.out.write(template.render({}))

  def post(self):
    name = self.request.get("name")
    if not name:
      self.response.out.write("Error: must supply a name")
      return
    if Player.all().filter("name =", name).count() > 0:
      self.response.out.write("A player with that name already exists")
      return

    player = Player(name=name)
    player.put()

    self.response.out.write("Successfully added " + name)

class AddGameHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/add_game.html")
    players = Player.all().run()
    args = {'players':players}
    self.response.out.write(template.render(args))

  def post(self):
    opponent = self.request.get("opponent")
    date_string = self.request.get("date")
    venue = self.request.get("venue")
    player_id_strings = self.request.get_all("players")

    date_tokens = date_string.split("/")
    date = datetime.date(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]))

    game = Game(opponent=opponent, date=date, venue=venue)
    player_ids = [int(pid) for pid in player_id_strings]
    players = Player.get_by_id(player_ids)
    player_keys = [p.key() for p in players]
    game.players = player_keys
    game.put()

    self.response.out.write("Successfully added game")

class GenerateTokenHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/generate_token.html")
    games = Game.all().run()
    players = Player.all().run()
    args = {'games':games,'players':players}
    self.response.out.write(template.render(args))

  def post(self):
    game_id = self.request.get("game")
    voter_id = self.request.get("player")

    voter = Player.get_by_id(int(voter_id))
    game = Game.get_by_id(int(game_id))

    value = base64.urlsafe_b64encode(os.urandom(32))
    token = Token(value=value, voter=voter, game=game, used=False)
    token.put()
    self.response.out.write(token.value)



app = webapp2.WSGIApplication([
  webapp2.Route('/admin/add_player', handler=AddPlayerHandler),
  webapp2.Route('/admin/add_game', handler=AddGameHandler),
  webapp2.Route('/admin/generate_token', handler=GenerateTokenHandler)
], debug=True)
