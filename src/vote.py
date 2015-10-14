import webapp2
import os
import jinja2
import logging

from models.game import Game
from models.player import Player
from models.vote import Vote

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

ERROR_DUPLICATE_VOTE = 1280
ERROR_VOTE_FOR_SELF = 1281

class VoteHandler(webapp2.RequestHandler):
  def get(self, token):
    # TODO: get this from token
    game = Game.all().get()
    players = Player.get(game.players)

    errmsg = None
    if self.request.get("err") == str(ERROR_DUPLICATE_VOTE):
      errmsg = "You can't vote for the same person twice"
    elif self.request.get("err") == str(ERROR_VOTE_FOR_SELF):
      errmsg = "You can't vote for yourself!"

    args = {'game':game, 'players':players, 'token':token, 'errmsg':errmsg}
    template = jinja_environment.get_template("templates/vote.html")
    self.response.out.write(template.render(args))

  def post(self):
    # TODO: get this from token
    game = Game.all().get()
    voter = Player.all().get()

    token = self.request.get("token")
    three = self.request.get("three")
    two = self.request.get("two")
    one = self.request.get("one")

    if one in [two, three] or two == three:
      return self.redirect("/vote/" + token + "?err=" + str(ERROR_DUPLICATE_VOTE))

    if str(voter.key().id()) in [one, two, three]:
      return self.redirect("/vote/" + token + "?err=" + str(ERROR_VOTE_FOR_SELF))

    three_player = Player.get_by_id(int(three))
    two_player = Player.get_by_id(int(two))
    one_player = Player.get_by_id(int(one))

    vote = Vote(game=game, three=three_player, two=two_player, one=one_player)
    vote.put()

    self.response.out.write("Vote submitted")

class SubmitHandler(webapp2.RequestHandler):
  def post(self):
    self.response.out.write("Submitted")

app = webapp2.WSGIApplication([
    webapp2.Route('/vote/<token>', handler=VoteHandler),
    webapp2.Route('/vote', handler=VoteHandler),
], debug=True)
