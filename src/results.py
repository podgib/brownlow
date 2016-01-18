import os
import jinja2
import logging
import operator
import webapp2

from google.appengine.ext import ndb

from models.game import Team
from models.game import Game
from models.game import GameResults
from models.vote import Vote
from models.vote import PlayerGameVotes, PlayerOverallVotes
from models.player import Player

def game_results(game):
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
  result = GameResults(game=game.key, three=players[0], two=players[1], one=players[2], voters=len(votes))

  return result

class OverallResults:
  def __init__(self, player_votes, game_votes):
    self.player_votes = player_votes
    self.game_votes = game_votes

def overall_results(team):
  games = Game.query(Game.team == team).order(Game.date).fetch(100)
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
