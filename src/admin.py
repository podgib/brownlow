import base64
import webapp2
import os
import re
import jinja2
import logging
import datetime

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import ndb

from models.player import Player
from models.game import Game, GameResults
from models.game import Team
from models.token import Token
from models.vote import Vote, SelfVote
from models.season import Season

from results import game_results, overall_results, OverallResults

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['teamString'] = Team.getString

ERROR_NO_NAME = 1280
ERROR_ALREADY_EXISTS = 1281
ERROR_NO_EMAIL = 1282
ERROR_INVALID_PHONE = 1283

mens_results_viewers = ['kyleturner24@gmail.com', 'eugene.duff@gmail.com']
womens_results_viewers = ['kyleturner24@gmail.com', 'eugene.duff@gmail.com']

class AddPlayerHandler(webapp2.RequestHandler):
  def get(self):
    errmsg = None
    if self.request.get("err") == str(ERROR_NO_NAME):
      errmsg = "You didn't supply a name"
    elif self.request.get("err") == str(ERROR_NO_EMAIL):
      errmsg = "You didn't supply an email"
    elif self.request.get("err") == str(ERROR_ALREADY_EXISTS):
      errmsg = "A player with that name already exists"
    elif self.request.get("err") == str(ERROR_INVALID_PHONE):
      errmsg = "Invalid phone number"
    template = jinja_environment.get_template("templates/add_edit_player.html")
    self.response.out.write(template.render({'errmsg':errmsg}))

  def post(self):
    name = self.request.get("name")
    email = self.request.get("email")
    phone = self.request.get("phone")
    if not name:
      self.redirect("http://vote.ouarfc.co.uk/admin/add_player?err=" + str(ERROR_NO_NAME))
      return
    if not email:
      self.redirect("http://vote.ouarfc.co.uk/admin/add_player?err=" + str(ERROR_NO_EMAIL))
      return
    if Player.query(Player.name == name).count() > 0:
      self.redirect("http://vote.ouarfc.co.uk/admin/add_player?err=" + str(ERROR_ALREADY_EXISTS))
      return

    player = Player(name=name, email=email)
    if phone:
      # Remove special characters
      phone = re.sub('[\s+=\-.]','',phone)
      # Place UK area code at start
      phone = re.sub('^0','44', phone)
      if phone.isdigit():
        player.phone = phone
    player.put()

    template = jinja_environment.get_template("templates/player_added.html")
    self.response.out.write(template.render({'name':name}))

class EditPlayerHandler(webapp2.RequestHandler):
  def get(self, player_id=None):
    if not player_id:
      template = jinja_environment.get_template("templates/player_list.html")
      players = Player.query().order(Player.name).fetch(1000)
      self.response.out.write(template.render({'players':players}))
      return

    errmsg = None
    if self.request.get("err") == str(ERROR_NO_NAME):
      errmsg = "You didn't supply a name"
    elif self.request.get("err") == str(ERROR_NO_EMAIL):
      errmsg = "You didn't supply an email"
    elif self.request.get("err") == str(ERROR_INVALID_PHONE):
      errmsg = "Invalid phone number"

    player = Player.get_by_id(int(player_id))
    if not player:
      self.response.out.write("Error: invalid player ID")
      logging.error("Invalid player ID: " + str(player_id))

    template = jinja_environment.get_template("templates/add_edit_player.html")
    self.response.out.write(template.render({'player':player, 'errmsg':errmsg}))

  def post(self):
    player_id = self.request.get("player_id")
    player = Player.get_by_id(int(player_id))
    if not player:
      self.response.out.write("Error: invalid player ID")
      logging.error("Invalid player ID: " + str(player_id))

    name = self.request.get("name")
    email = self.request.get("email")
    phone = self.request.get("phone")

    if not name:
      self.redirect(
          "http://vote.ouarfc.co.uk/admin/edit_player/" + str(player_id) + "?err=" + str(ERROR_NO_NAME))
      return

    if not email:
      self.redirect(
          "http://vote.ouarfc.co.uk/admin/edit_player/" + str(player_id) + "?err=" + str(ERROR_NO_EMAIL))
      return

    if phone:
      # Remove special characters
      phone = re.sub('[\s+=\-.]','',phone)
      # Place UK area code at start
      phone = re.sub('^0','44', phone)
      if phone.isdigit():
        player.phone = phone
      else:
        self.redirect(
          "http://vote.ouarfc.co.uk/admin/edit_player/" + str(player_id) + "?err=" + str(ERROR_INVALID_PHONE))
        return
    else:
      player.phone = None

    player.name = name
    player.email = email
    player.put()

    template = jinja_environment.get_template("templates/player_saved.html")
    self.response.out.write(template.render({'name':name}))

class EditGameHandler(webapp2.RequestHandler):
  def get(self, game_id=None):
    if not game_id:
      template = jinja_environment.get_template("templates/game_list.html")
      games = Game.query().order(Game.date).fetch(100)
      self.response.out.write(template.render({'games':games}))
      return

    game = Game.get_by_id(int(game_id))
    if not game:
      self.response.out.write("Error: invalid game ID")
      logging.error("Invalid game ID: " + str(game_id))
      return

    teams = Team.getAll();

    players = Player.query().order(Player.name).fetch(100)
    playing = [p for p in players if p.key in game.players]
    not_playing = [p for p in players if p.key not in game.players]

    template = jinja_environment.get_template("templates/add_edit_game.html")
    args = {'playing':playing,'not_playing':not_playing,'game':game, 'teams':teams}
    self.response.out.write(template.render(args))

  def post(self):
    game_id = self.request.get("game_id")
    game = Game.get_by_id(int(game_id))
    if not game:
      self.response.out.write("Error: invalid game ID")
      logging.error("Invalid game ID: " + str(game_id))
      return

    if self.request.get("delete"):
      self.delete_game(game)
      template = jinja_environment.get_template("templates/game_deleted.html")
      self.response.out.write(template.render())
      return

    opponent = self.request.get("opponent")
    date_string = self.request.get("date")
    venue = self.request.get("venue")
    player_id_strings = self.request.get_all("players")
    team = Team.getTeam(self.request.get("team"))
    weight = float(self.request.get("weight"))

    date_tokens = date_string.split("/")
    if len(date_tokens) == 1:
      date_tokens = date_string.split("-")
    if int(date_tokens[0]) < 100:
      date_tokens.reverse()
    date = datetime.date(int(date_tokens[0]), int(date_tokens[1]), int(date_tokens[2]))

    game.opponent = opponent
    game.date = date
    game.venue = venue
    game.team = team
    game.weight = weight
    player_keys = [ndb.Key('Player', int(pid)) for pid in player_id_strings]
    game.players = player_keys
    game.put()

    template = jinja_environment.get_template("templates/game_saved.html")
    self.response.out.write(template.render({}))

  def delete_game(self, game):
    tokens = Token.query(Token.game == game.key)
    keys = [token.key for token in tokens]
    votes = Vote.query(Vote.game == game.key)
    keys.extend([vote.key for vote in votes])
    votes = SelfVote.query(SelfVote.game == game.key)
    keys.extend([vote.key for vote in votes])
    results = GameResults.query(GameResults.game == game.key)
    keys.extend([result.key for result in results])
    ndb.delete_multi_async(keys)
    game.key.delete()


class AddGameHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/add_edit_game.html")
    players = Player.query().order(Player.name).fetch(1000)
    teams = Team.getAll()
    args = {'players':players, 'teams':teams}
    self.response.out.write(template.render(args))

  def post(self):
    opponent = self.request.get("opponent")
    date_string = self.request.get("date")
    venue = self.request.get("venue")
    player_id_strings = self.request.get_all("players")
    team = Team.getTeam(self.request.get("team"))
    weight = float(self.request.get("weight"))

    date_tokens = date_string.split("/")
    if len(date_tokens) == 1:
      date_tokens = date_string.split("-")
    if int(date_tokens[0]) < 100:
      date_tokens.reverse()
    date = datetime.date(int(date_tokens[0]), int(date_tokens[1]), int(date_tokens[2]))

    game = Game(opponent=opponent, date=date, venue=venue, team=team, weight=weight)
    player_keys = [ndb.Key('Player', int(pid)) for pid in player_id_strings]
    game.players = player_keys
    game.put()

    template = jinja_environment.get_template("templates/game_added.html")
    self.response.out.write(template.render({}))

class GenerateTokenHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/generate_token.html")
    games = Game.query().order(Game.date).fetch(100)
    players = Player.query().order(Player.name).fetch(1000)
    args = {'games':games,'players':players}
    self.response.out.write(template.render(args))

  def post(self):
    game_id = self.request.get("game")
    voter_id = self.request.get("player")

    voter = Player.get_by_id(int(voter_id))
    game = Game.get_by_id(int(game_id))

    value = base64.urlsafe_b64encode(os.urandom(16))
    token = Token(value=value, voter=voter.key, game=game.key, used=False)
    token.put()
    url = "http://vote.ouarfc.co.uk/vote/" + value
    self.response.out.write(url)

class EmailHandler(webapp2.RequestHandler):
  def get(self, game_id=None):
    if not game_id:
      template = jinja_environment.get_template("templates/email_list.html")
      games = Game.query().order(Game.date).fetch(100)
      self.response.out.write(template.render({'games':games}))
      return

    game = Game.get_by_id(int(game_id))
    if not game:
      self.response.out.write("Error: invalid game ID")
      logging.error("Invalid game ID: " + str(game_id))
      return

    players = Player.query().order(Player.name).fetch(100)
    playing = [p for p in players if p.key in game.players]
    not_playing = [p for p in players if p.key not in game.players]

    template = jinja_environment.get_template("templates/send_emails.html")
    args = {'playing':playing,'not_playing':not_playing,'game':game}
    self.response.out.write(template.render(args))

  def post(self):
    game_id = self.request.get('game')
    player_ids = self.request.get_all('players')

    game = Game.get_by_id(int(game_id))

    player_keys = [ndb.Key('Player', int(pid)) for pid in player_ids]
    players = ndb.get_multi(player_keys)
    game.players = player_keys
    game.put()

    params = {'player':0, 'game':game_id}
    for p in players:
      params['player'] = p.key.id()
      taskqueue.add(url='/worker/email', params=params, queue_name='email', countdown=0)
      logging.info('Submitted task to email' + p.email)

    template = jinja_environment.get_template("templates/emails_sent.html")
    self.response.out.write(template.render({}))

class ResultsHandler(webapp2.RequestHandler):

  def get(self, team_name):
    team = Team.getTeam(team_name)
    if not team:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg':'Invalid team: ' + team_name}))
      return

    results = overall_results(team)

    user_email = users.get_current_user().email()
    authorised = True
    if team == Team.MEN:
      authorised = user_email in mens_results_viewers
    if team == Team.WOMEN:
      authorised = user_email in womens_results_viewers

    params = {'team':team, 'results':results, 'authorised':authorised}
    template = jinja_environment.get_template("templates/results.html")
    self.response.out.write(template.render(params))

class VotersHandler(webapp2.RequestHandler):
  def get(self, game_id):
    game = Game.get_by_id(int(game_id))
    if not game:
      self.response.out.write("Error: invalid game ID")
      logging.error("Invalid game ID: " + str(game_id))
      return

    voters = Token.query(ndb.AND(Token.game == game.key, Token.used == True)).fetch(100)
    non_voters = Token.query(ndb.AND(Token.game == game.key, Token.used == False)).fetch(100)

    template = jinja_environment.get_template('templates/voters.html')
    params = {'voters':voters,'non_voters':non_voters,'game':game}
    self.response.out.write(template.render(params))

class PublicResultsHandler(webapp2.RequestHandler):
  def get(self):
    teams = Team.getAll()
    season = Season.query().get()
    template = jinja_environment.get_template("templates/results_rounds.html")
    self.response.out.write(template.render({'teams': teams, 'season': season}))

  def post(self):
    teams = Team.getAll()
    season = Season.query().get()

    for team in teams:
      round = int(self.request.get(team.lower()))
      idx = Team.getTeam(team)
      if idx < 0:
        idx = idx % len(teams)
      else:
        idx = idx - 1
      season.public_round[idx] = round

    season.put()

    template = jinja_environment.get_template("templates/results_rounds.html")
    self.response.out.write(template.render({'teams': teams, 'season': season}))


class MenuHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('templates/admin.html')
    self.response.out.write(template.render({}))

class ResultsMenuHandler(webapp2.RequestHandler):
  def get(self):
    teams = Team.getAll()
    template = jinja_environment.get_template("templates/results_menu.html")
    self.response.out.write(template.render({'teams': teams}))


app = webapp2.WSGIApplication([
  webapp2.Route('/admin/add_player', handler=AddPlayerHandler),
  webapp2.Route('/admin/add_game', handler=AddGameHandler),
  webapp2.Route('/admin/edit_player', handler=EditPlayerHandler),
  webapp2.Route('/admin/edit_player/<player_id>', handler=EditPlayerHandler),
  webapp2.Route('/admin/edit_game', handler=EditGameHandler),
  webapp2.Route('/admin/edit_game/<game_id>', handler=EditGameHandler),
  webapp2.Route('/admin/generate_token', handler=GenerateTokenHandler),
  webapp2.Route('/admin/send_emails', handler=EmailHandler),
  webapp2.Route('/admin/send_emails/<game_id>', handler=EmailHandler),
  ('/admin/results', ResultsMenuHandler),
  ('/admin/results/public', PublicResultsHandler),
  webapp2.Route('/admin/results/<team_name>', handler=ResultsHandler),
  webapp2.Route('/admin/voters/<game_id>', handler=VotersHandler),
  ('/admin',MenuHandler), ('/admin/', MenuHandler)
], debug=True)
