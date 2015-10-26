import base64
import webapp2
import os
import jinja2
import logging
import datetime

from google.appengine.api import taskqueue

from models.player import Player
from models.game import Game
from models.game import Team
from models.token import Token

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['teamString'] = Team.getString

ERROR_NO_NAME = 1280
ERROR_ALREADY_EXISTS = 1281
ERROR_NO_EMAIL = 1282

class AddPlayerHandler(webapp2.RequestHandler):
  def get(self):
    errmsg = None
    if self.request.get("err") == str(ERROR_NO_NAME):
      errmsg = "You didn't supply a name"
    elif self.request.get("err") == str(ERROR_NO_EMAIL):
      errmsg = "You didn't supply an email"
    elif self.request.get("err") == str(ERROR_ALREADY_EXISTS):
      errmsg = "A player with that name already exists"
    template = jinja_environment.get_template("templates/add_player.html")
    self.response.out.write(template.render({'errmsg':errmsg}))

  def post(self):
    name = self.request.get("name")
    email = self.request.get("email")
    if not name:
      self.redirect("http://vote.ouarfc.co.uk/admin/add_player?err=" + str(ERROR_NO_NAME))
      return
    if not email:
      self.redirect("http://vote.ouarfc.co.uk/admin/add_player?err=" + str(ERROR_NO_EMAIL))
      return
    if Player.all().filter("name =", name).count() > 0:
      self.redirect("http://vote.ouarfc.co.uk/admin/add_player?err=" + str(ERROR_ALREADY_EXISTS))
      return

    player = Player(name=name, email=email)
    player.put()

    template = jinja_environment.get_template("templates/player_added.html")
    self.response.out.write(template.render({'name':name}))

class AddGameHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/add_game.html")
    players = Player.all().order('name').run()
    teams = Team.getAll()
    args = {'players':players, 'teams':teams}
    self.response.out.write(template.render(args))

  def post(self):
    opponent = self.request.get("opponent")
    date_string = self.request.get("date")
    venue = self.request.get("venue")
    player_id_strings = self.request.get_all("players")
    team = Team.getTeam(self.request.get("team"))

    date_tokens = date_string.split("/")
    if len(date_tokens) == 1:
      date_tokens = date_string.split("-")
    if int(date_tokens[0]) < 100:
      date_tokens.reverse()
    date = datetime.date(int(date_tokens[0]), int(date_tokens[1]), int(date_tokens[2]))

    game = Game(opponent=opponent, date=date, venue=venue, team=team)
    player_ids = [int(pid) for pid in player_id_strings]
    players = Player.get_by_id(player_ids)
    player_keys = [p.key() for p in players]
    game.players = player_keys
    game.put()

    template = jinja_environment.get_template("templates/game_added.html")
    self.response.out.write(template.render({}))

class GenerateTokenHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/generate_token.html")
    games = Game.all().order('date').run()
    players = Player.all().order('name').run()
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
    url = "http://vote.ouarfc.co.uk/vote/" + value
    self.response.out.write(url)

class EmailHandler(webapp2.RequestHandler):
  def get(self, game_id=None):
    if not game_id:
      template = jinja_environment.get_template("templates/game_list.html")
      games = Game.all().order('date').run()
      self.response.out.write(template.render({'games':games}))
      return

    game = Game.get_by_id(int(game_id))
    if not game:
      self.response.out.write("Error: invalid game ID")
      logging.error("Invalid game ID: " + str(game_id))
      return

    players = Player.all().order('name').fetch(100)
    playing = [p for p in players if p.key() in game.players]
    not_playing = [p for p in players if p.key() not in game.players]

    template = jinja_environment.get_template("templates/send_emails.html")
    args = {'playing':playing,'not_playing':not_playing,'game':game}
    self.response.out.write(template.render(args))

  def post(self):
    game_id = self.request.get('game')
    player_ids = self.request.get_all('players')

    player_ids = [int(p) for p in player_ids]
    game = Game.get_by_id(int(game_id))
    players = Player.get_by_id(player_ids)

    player_keys = [p.key() for p in players]
    game.players = player_keys
    game.put()

    params = {'player':0, 'game':game_id}
    for p in players:
      params['player'] = p.key().id()
      taskqueue.add(url='/worker/email', params=params, queue_name='email', countdown=0)
      logging.info('Submitted task to email' + p.email)

    template = jinja_environment.get_template("templates/emails_sent.html")
    self.response.out.write(template.render({}))

class MenuHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('templates/admin.html')
    self.response.out.write(template.render({}))

app = webapp2.WSGIApplication([
  webapp2.Route('/admin/add_player', handler=AddPlayerHandler),
  webapp2.Route('/admin/add_game', handler=AddGameHandler),
  webapp2.Route('/admin/generate_token', handler=GenerateTokenHandler),
  webapp2.Route('/admin/send_emails', handler=EmailHandler),
  webapp2.Route('/admin/send_emails/<game_id>', handler=EmailHandler),
  ('/admin',MenuHandler), ('/admin/', MenuHandler)
], debug=True)
