import os
import jinja2
import logging
import operator
import webapp2
import json

from google.appengine.ext import ndb

from models.game import Team
from models.game import Game
from models.game import GameResults
from models.vote import Vote
from models.season import Season
from models.vote import PlayerGameVotes, PlayerOverallVotes
from models.player import Player

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['teamString'] = Team.getString

@ndb.transactional
def cache_results(results):
  if GameResults.query(ancestor=results.game).count() == 0:
    results.put()

def full_game_results(game):
  votes = Vote.query(Vote.game == game.key).fetch(1000)
  player_votes = {}

  for vote in votes:
    p = vote.three
    if player_votes.has_key(p):
      player_votes[p].threes += 1
    else:
      player_votes[p] = PlayerGameVotes(game=game.key, player=p, threes=1)

    p = vote.two
    if player_votes.has_key(p):
      player_votes[p].twos += 1
    else:
      player_votes[p] = PlayerGameVotes(game=game.key, player=p, twos=1)

    p = vote.one
    if player_votes.has_key(p):
      player_votes[p].ones += 1
    else:
      player_votes[p] = PlayerGameVotes(game=game.key, player=p, ones=1)

  if len(player_votes) < 3:
    return None

  sorted_votes = sorted(player_votes.items(), key=lambda p: -p[1].ranking_points())
  votes = [(p[0].get().name, p[1].total()) for p in sorted_votes]
  return votes

def game_results(game):
  cached_results = GameResults.query(ancestor=game.key).get()
  if cached_results:
    return cached_results

  votes = Vote.query(Vote.game == game.key).fetch(1000)

  player_votes = {}

  for vote in votes:
    three = vote.three
    if player_votes.has_key(three):
      player_votes[three].threes += 1
    else:
      player_votes[three] = PlayerGameVotes(game=game.key, player=three, threes=1)

    two = vote.two
    if player_votes.has_key(two):
      player_votes[two].twos += 1
    else:
      player_votes[two] = PlayerGameVotes(game=game.key, player=two, twos=1)

    one = vote.one
    if player_votes.has_key(one):
      player_votes[one].ones += 1
    else:
      player_votes[one] = PlayerGameVotes(game=game.key, player=one, ones=1)

  if len(player_votes) < 3:
    # No votes cast
    return None

  sorted_votes = sorted(player_votes.items(), key=lambda p: -p[1].ranking_points())
  players = [sorted_votes[0][0], sorted_votes[1][0], sorted_votes[2][0]]
  result = GameResults(parent=game.key, game=game.key, three=players[0], two=players[1], one=players[2], voters=len(votes))

  cache_results(result)
  return result

class OverallResults:
  def __init__(self, player_votes, game_votes):
    self.player_votes = player_votes
    self.game_votes = game_votes

def overall_results(team, rounds = 100):
  games = Game.query(Game.team == team).order(Game.date).fetch(rounds)
  game_votes = []
  player_votes = {}

  for game in games:
    results = game_results(game)
    if not results:
      continue

    if player_votes.has_key(results.three):
      player_votes[results.three].threes +=1
      player_votes[results.three].total += 3 * game.weight
    else:
      player_votes[results.three] = \
        PlayerOverallVotes(player=results.three, threes=1, total=3*game.weight)

    if player_votes.has_key(results.two):
      player_votes[results.two].twos +=1
      player_votes[results.two].total +=2 * game.weight
    else:
      player_votes[results.two] = \
        PlayerOverallVotes(player=results.two, twos=1, total=2*game.weight)

    if player_votes.has_key(results.one):
      player_votes[results.one].ones +=1
      player_votes[results.one].total +=1 * game.weight
    else:
      player_votes[results.one] = \
        PlayerOverallVotes(player=results.one, ones=1, total=game.weight)

    game_votes.append(results)

  sorted_votes = sorted(player_votes.items(), key=lambda p: -p[1].ranking_points())
  return OverallResults(player_votes=[r[1] for r in sorted_votes], game_votes=game_votes)

class ResultsHandler(webapp2.RequestHandler):

  def get(self, team_name):
    team = Team.getTeam(team_name)
    if not team:
      template = jinja_environment.get_template("templates/error.html")
      self.response.out.write(template.render({'errmsg':'Invalid team: ' + team_name}))
      return

    season = Season.query().get()
    if not season:
      season = Season(public_round=[0 for t in Team.getAll()])
      season.put()

    round = season.public_round[team - 1]

    if round > 0:
      results = overall_results(team, round)
    else:
      results = None

    params = {'team':team, 'team_name': Team.getString(team), 'round': round, 'results':results, 'authorised':True,
              'hide_count':True, 'refresh': True}
    template = jinja_environment.get_template("templates/results.html")
    self.response.out.write(template.render(params))

class ResultsMenuHandler(webapp2.RequestHandler):
  def get(self):
    teams = Team.getAll()[:-1]
    template = jinja_environment.get_template("templates/results_menu.html")
    self.response.out.write(template.render({'teams': teams, 'public': True}))

class RoundHandler(webapp2.RequestHandler):
  def get(self):
    season = Season.query().get()
    data = {}
    for team in Team.getAll():
      data[team] = season.get_public_round(team)
    self.response.out.write(json.dumps(data))
    self.response.content_type = 'application/json'

app = webapp2.WSGIApplication([
  ('/results/round', RoundHandler),
  webapp2.Route('/results/<team_name>', handler=ResultsHandler),
  ('/results', ResultsMenuHandler),
], debug=True)
