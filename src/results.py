import os
import jinja2
import logging
import operator
import webapp2

from models.game import Team
from models.game import Game
from models.vote import Vote
from models.vote import PlayerGameVotes
from models.player import Player

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['teamString'] = Team.getString

class MenuHandler(webapp2.RequestHandler):
  def get(self):
    teams = Team.getAll()
    template = jinja_environment.get_template("templates/results_menu.html")
    self.response.out.write(template.render({'teams': teams}))

def game_results(game):
  votes = Vote.all().filter("game =", game).run()

  player_votes = {}

  for vote in votes:
    three = vote.three
    if player_votes.has_key(three.key()):
      player_votes[three.key()].threes += 1
    else:
      player_votes[three.key()] = PlayerGameVotes(game=game, player=three, threes=1)

    two = vote.two
    if player_votes.has_key(two.key()):
      player_votes[two.key()].twos += 1
    else:
      player_votes[two.key()] = PlayerGameVotes(game=game, player=two, twos=1)

    one = vote.one
    if player_votes.has_key(one.key()):
      player_votes[one.key()].ones += 1
    else:
      player_votes[one.key()] = PlayerGameVotes(game=game, player=one, ones=1)

  if len(player_votes) < 3:
    # No votes cast
    return None

  sorted_votes = sorted(player_votes.items(), key=lambda p: -p[1].ranking_points())

  return {'three': sorted_votes[0][0], 'two': sorted_votes[1][0], 'one': sorted_votes[2][0]}

class ResultsHandler(webapp2.RequestHandler):

  def get(self, team_name):
    team = Team.getTeam(team_name)
    if not team:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg':'Invalid team: ' + team_name}))
      return

    games = Game.all().filter("team =", team).run()


app = webapp2.WSGIApplication([
  ('/results', MenuHandler),
  webapp2.Route('/results/<team_name>', handler=ResultsHandler)
], debug=True)
