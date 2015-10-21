import os
import jinja2
import logging
import operator
import webapp2

from models.game import Team
from models.game import Game
from models.vote import Vote

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
      player_votes[three.key()] = player_votes[three.key()] + 3
    else:
      player_votes[three.key()] = 3

    two = vote.two
    if player_votes.has_key(two.key()):
      player_votes[two.key()] = player_votes[two.key()] + 3
    else:
      player_votes[two.key()] = 3

    one = vote.one
    if player_votes.has_key(one.key()):
      player_votes[one.key()] = player_votes[one.key()] + 3
    else:
      player_votes[one.key()] = 3

  sorted_votes = sorted(player_votes.items(), key=-operator.itemgetter(1))

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
