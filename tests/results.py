import sys

import unittest
import datetime

from google.appengine.ext import testbed
from google.appengine.ext import db

from src.models.game import Game, Team
from src.models.player import Player
from src.models.vote import Vote
from src.models.token import Token
from src.results import game_results, overall_results

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

    self.assertEqual('Player 4', results.three.name)
    self.assertEqual('Player 7', results.two.name)
    self.assertEqual('Player 1', results.one.name)

  def testOverallResults(self):
    team = Team.TEST
    results = overall_results(team)

    self.assertEqual('Player 4', results[0].player.name)
    self.assertEqual('Player 7', results[1].player.name)
    self.assertEqual('Player 1', results[2].player.name)

  def tearDown(self):
    self.testbed.deactivate()

class NoVotesTestCase(unittest.TestCase):
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

  def testGameResults(self):
    g = Game.all().get()

    results = game_results(g)

    self.assertIsNone(results)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    self.assertEqual(0, len(results))

  def tearDown(self):
    self.testbed.deactivate()

class TieBreakTestCase(unittest.TestCase):
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

    # Rankings:
    # Player 3 - 7 votes (two threes)
    # Player 4 - 7 votes (one three, two twos)
    # Player 7 - 7 votes (one three, one two)
    v = Vote(game=g, three=players[3], two=players[4], one=players[7])
    v.put()
    v = Vote(game=g, three=players[7], two=players[4], one=players[5])
    v.put()
    v = Vote(game=g, three=players[3], two=players[9], one=players[7])
    v.put()
    v = Vote(game=g, three=players[4], two=players[7], one=players[3])
    v.put()

  def testGameResults(self):
    g = Game.all().get()
    results = game_results(g)

    self.assertEqual('Player 3', results.three.name)
    self.assertEqual('Player 4', results.two.name)
    self.assertEqual('Player 7', results.one.name)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    self.assertEqual('Player 3', results[0].player.name)
    self.assertEqual('Player 4', results[1].player.name)
    self.assertEqual('Player 7', results[2].player.name)

  def tearDown(self):
    self.testbed.deactivate()

class TwoMatchTestCase(unittest.TestCase):
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()

    self.g1 = Game(opponent='test', date=datetime.date.today(), venue='test', team=Team.TEST)
    self.g2 = Game(opponent='test', date=datetime.date.today(), venue='test', team=Team.TEST)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    self.g1.players = [p.key() for p in players]
    self.g1.put()

    self.g2.players = [p.key() for p in players]
    self.g2.put()

    v = Vote(game=self.g1, three=players[7], two=players[9], one=players[3])
    v.put()
    v = Vote(game=self.g1, three=players[4], two=players[7], one=players[3])
    v.put()
    v = Vote(game=self.g2, three=players[3], two=players[4], one=players[7])
    v.put()

  def testGameResults(self):
    results = game_results(self.g1)

    self.assertEqual('Player 7', results.three.name)
    self.assertEqual('Player 4', results.two.name)
    self.assertEqual('Player 9', results.one.name)

    results = game_results(self.g2)
    self.assertEqual('Player 3', results.three.name)
    self.assertEqual('Player 4', results.two.name)
    self.assertEqual('Player 7', results.one.name)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    self.assertEqual('Player 7', results[0].player.name)
    self.assertEqual('Player 4', results[1].player.name)
    self.assertEqual('Player 3', results[2].player.name)
    self.assertEqual('Player 9', results[3].player.name)

  def tearDown(self):
    self.testbed.deactivate()

if __name__ == '__main__':
  unittest.main()