import os
import jinja2
import logging
import operator
import webapp2

from models.game import Team
from models.game import Game
from models.game import GameResults
from models.vote import Vote
from models.vote import PlayerGameVotes, PlayerOverallVotes
from models.player import Player

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
  players = Player.get([sorted_votes[0][0], sorted_votes[1][0], sorted_votes[2][0]])
  result = GameResults(game=game, three=players[0], two=players[1], one=players[2])

  return result

class OverallResults:
  def __init__(self, player_votes, game_votes):
    self.player_votes = player_votes
    self.game_votes = game_votes

def overall_results(team):
  games = Game.all().filter("team =", team).order("date").run()
  game_votes = []
  player_votes = {}

  for game in games:
    results = game_results(game)
    if not results:
      continue

    if player_votes.has_key(results.three.key()):
      player_votes[results.three.key()].threes +=1
    else:
      player_votes[results.three.key()] = PlayerOverallVotes(player=results.three, threes=1)

    if player_votes.has_key(results.two.key()):
      player_votes[results.two.key()].twos +=1
    else:
      player_votes[results.two.key()] = PlayerOverallVotes(player=results.two, twos=1)

    if player_votes.has_key(results.one.key()):
      player_votes[results.one.key()].ones +=1
    else:
      player_votes[results.one.key()] = PlayerOverallVotes(player=results.one, ones=1)

    game_votes.append(results)

  sorted_votes = sorted(player_votes.items(), key=lambda p: -p[1].ranking_points())
  return OverallResults(player_votes=[r[1] for r in sorted_votes], game_votes=game_votes)
