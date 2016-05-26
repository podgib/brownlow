from google.appengine.api.taskqueue import taskqueue
import webapp2
import os
import jinja2
import logging

from google.appengine.ext import ndb
from google.appengine.api import mail

from models.game import Team
from models.game import GameResults
from models.player import Player
from models.vote import Vote
from models.token import Token

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['teamString'] = Team.getString

ERROR_DUPLICATE_VOTE = 1280
ERROR_VOTE_FOR_SELF = 1281

class VoteHandler(webapp2.RequestHandler):
  def get(self, token_string):
    token = Token.query(Token.value == token_string).get()
    if not token:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg': "invalid voting token"}))
      return
    if token.used:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg': "You've already voted!"}))
      return

    voter = token.voter.get();

    game = token.game.get()
    players = ndb.get_multi(game.players)
    players.sort(key=lambda p: p.name)

    errmsg = None
    if self.request.get("err") == str(ERROR_DUPLICATE_VOTE):
      errmsg = "You can't vote for the same person twice"
    elif self.request.get("err") == str(ERROR_VOTE_FOR_SELF):
      errmsg = "You can't vote for yourself!"

    args = {'game':game, 'players':players, 'token':token.value, 'errmsg':errmsg, 'voter':voter}
    template = jinja_environment.get_template("templates/vote.html")
    self.response.out.write(template.render(args))

  def post(self):
    token_string = self.request.get("token")
    token = Token.query(Token.value == token_string).get()
    if not token:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg': "invalid voting token"}))
      return
    if token.used:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg': "You've already voted!"}))
      return

    game = token.game
    voter = token.voter

    three = self.request.get("three")
    two = self.request.get("two")
    one = self.request.get("one")

    if one in [two, three] or two == three:
      return self.redirect("/vote/" + token.value + "?err=" + str(ERROR_DUPLICATE_VOTE))

    if str(voter.id()) in [one, two, three]:
      return self.redirect("/vote/" + token.value + "?err=" + str(ERROR_VOTE_FOR_SELF))

    three_player = Player.get_by_id(int(three))
    two_player = Player.get_by_id(int(two))
    one_player = Player.get_by_id(int(one))

    vote = Vote(game=game, three=three_player.key, two=two_player.key, one=one_player.key)
    token.used = True

    vote.put()
    token.put()

    cached_results = GameResults.query(GameResults.game == game).fetch()
    for r in cached_results:
      r.delete()

    template = jinja_environment.get_template('templates/success.html')
    self.response.out.write(template.render({}))

class SelfHandler(webapp2.RequestHandler):
  def get(self, token_string):
    logging.info("Received a self vote")
    num_votes = self.request.get("votes")

    params = {'token':token_string, 'votes':num_votes}
    taskqueue.add(url='/worker/self_vote', params=params, queue_name='email', countdown=0)
    self.response.out.write("Success!")


class LandingHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('templates/landing.html')
    self.response.out.write(template.render({}))

app = webapp2.WSGIApplication([
    webapp2.Route('/vote/<token_string>', handler=VoteHandler),
    webapp2.Route('/vote', handler=VoteHandler),
    webapp2.Route('/vote/self/<token_string>', handler=SelfHandler),
  ('/', LandingHandler)
], debug=True)
