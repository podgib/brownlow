import sys

import unittest
import datetime

from google.appengine.ext import testbed
from google.appengine.ext import db

from src.models.game import Game, Team
from src.models.player import Player
from src.models.vote import Vote
from src.models.token import Token
from src.results import game_results

class SingleGameTestCase(unittest.TestCase):
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()

    g = Game(opponent='test', date=datetime.date.today(), venue='test', team=Team.TEST)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    g.players = [p.key() for p in players]
    g.put()

    for i in range(0, 10):
      v = Vote(game=g, three=players[4], two=players[7], one=players[1])
      v.put()

  def testGameResults(self):
    g = Game.all().get()
    results = game_results(g)

    three = Player.get(results['three'])
    two = Player.get(results['two'])
    one = Player.get(results['one'])

    self.assertEqual('Player 4', three.name)
    self.assertEqual('Player 7', two.name)
    self.assertEqual('Player 1', one.name)

  def tearDown(self):
    self.testbed.deactivate()

if __name__ == '__main__':
  unittest.main()