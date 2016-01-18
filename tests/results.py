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
    self.testbed.init_memcache_stub()

    g = Game(opponent='test', date=datetime.date.today(), venue='test', team=Team.TEST)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    g.players = [p.key for p in players]
    g.put()

    for i in range(0, 10):
      v = Vote(game=g.key, three=players[4].key, two=players[7].key, one=players[1].key)
      v.put()

  def testGameResults(self):
    g = Game.query().get()
    results = game_results(g)

    self.assertEqual('Player 4', results.three.get().name)
    self.assertEqual('Player 7', results.two.get().name)
    self.assertEqual('Player 1', results.one.get().name)
    self.assertEqual(10, results.voters)

  def testOverallResults(self):
    team = Team.TEST
    results = overall_results(team)

    # Overall rankings
    self.assertEqual('Player 4', results.player_votes[0].player.get().name)
    self.assertEqual('Player 7', results.player_votes[1].player.get().name)
    self.assertEqual('Player 1', results.player_votes[2].player.get().name)

    # Per-game rankings
    self.assertEqual('Player 4', results.game_votes[0].three.get().name)
    self.assertEqual('Player 7', results.game_votes[0].two.get().name)
    self.assertEqual('Player 1', results.game_votes[0].one.get().name)
    self.assertEqual(10, results.game_votes[0].voters)

  def tearDown(self):
    self.testbed.deactivate()

class NoVotesTestCase(unittest.TestCase):
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()

    g = Game(opponent='test', date=datetime.date.today(), venue='test', team=Team.TEST)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    g.players = [p.key for p in players]
    g.put()

  def testGameResults(self):
    g = Game.query().get()

    results = game_results(g)

    self.assertIsNone(results)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    self.assertEqual(0, len(results.player_votes))
    self.assertEqual(0, len(results.game_votes))

  def tearDown(self):
    self.testbed.deactivate()

class TieBreakTestCase(unittest.TestCase):
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()

    g = Game(opponent='test', date=datetime.date.today(), venue='test', team=Team.TEST)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    g.players = [p.key for p in players]
    g.put()

    # Rankings:
    # Player 3 - 7 votes (two threes)
    # Player 4 - 7 votes (one three, two twos)
    # Player 7 - 7 votes (one three, one two)
    v = Vote(game=g.key, three=players[3].key, two=players[4].key, one=players[7].key)
    v.put()
    v = Vote(game=g.key, three=players[7].key, two=players[4].key, one=players[5].key)
    v.put()
    v = Vote(game=g.key, three=players[3].key, two=players[9].key, one=players[7].key)
    v.put()
    v = Vote(game=g.key, three=players[4].key, two=players[7].key, one=players[3].key)
    v.put()

  def testGameResults(self):
    g = Game.query().get()
    results = game_results(g)

    self.assertEqual('Player 3', results.three.get().name)
    self.assertEqual('Player 4', results.two.get().name)
    self.assertEqual('Player 7', results.one.get().name)
    self.assertEqual(4, results.voters)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    # Overall rankings
    self.assertEqual('Player 3', results.player_votes[0].player.get().name)
    self.assertEqual('Player 4', results.player_votes[1].player.get().name)
    self.assertEqual('Player 7', results.player_votes[2].player.get().name)

    # Per-game votes
    self.assertEqual('Player 3', results.game_votes[0].three.get().name)
    self.assertEqual('Player 4', results.game_votes[0].two.get().name)
    self.assertEqual('Player 7', results.game_votes[0].one.get().name)
    self.assertEqual(4, results.game_votes[0].voters)

  def tearDown(self):
    self.testbed.deactivate()

class TwoMatchTestCase(unittest.TestCase):
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()

    self.g1 = Game(opponent='test', date=datetime.date(2015, 10, 01), venue='test', team=Team.TEST)
    self.g2 = Game(opponent='test', date=datetime.date(2015, 11, 01), venue='test', team=Team.TEST)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    self.g1.players = [p.key for p in players]
    self.g1.put()

    self.g2.players = [p.key for p in players]
    self.g2.put()

    v = Vote(game=self.g1.key, three=players[7].key, two=players[9].key, one=players[3].key)
    v.put()
    v = Vote(game=self.g1.key, three=players[4].key, two=players[7].key, one=players[3].key)
    v.put()
    v = Vote(game=self.g2.key, three=players[3].key, two=players[4].key, one=players[7].key)
    v.put()

  def testGameResults(self):
    results = game_results(self.g1)

    self.assertEqual('Player 7', results.three.get().name)
    self.assertEqual('Player 4', results.two.get().name)
    self.assertEqual('Player 9', results.one.get().name)
    self.assertEqual(2, results.voters)

    results = game_results(self.g2)
    self.assertEqual('Player 3', results.three.get().name)
    self.assertEqual('Player 4', results.two.get().name)
    self.assertEqual('Player 7', results.one.get().name)
    self.assertEqual(1, results.voters)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    # Overall rankings
    self.assertEqual('Player 7', results.player_votes[0].player.get().name)
    self.assertEqual('Player 4', results.player_votes[1].player.get().name)
    self.assertEqual('Player 3', results.player_votes[2].player.get().name)
    self.assertEqual('Player 9', results.player_votes[3].player.get().name)

    # Game 1
    self.assertEqual('Player 7', results.game_votes[0].three.get().name)
    self.assertEqual('Player 4', results.game_votes[0].two.get().name)
    self.assertEqual('Player 9', results.game_votes[0].one.get().name)
    self.assertEqual(2, results.game_votes[0].voters)

    # Game 2
    self.assertEqual('Player 3', results.game_votes[1].three.get().name)
    self.assertEqual('Player 4', results.game_votes[1].two.get().name)
    self.assertEqual('Player 7', results.game_votes[1].one.get().name)
    self.assertEqual(1, results.game_votes[1].voters)

  def tearDown(self):
    self.testbed.deactivate()

class WeightedTestCase(unittest.TestCase):
  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()

    self.g1 = \
      Game(opponent='test', date=datetime.date(2015, 10, 01), venue='test', team=Team.TEST, weight=0.4)
    self.g2 = \
      Game(opponent='test', date=datetime.date(2015, 11, 01), venue='test', team=Team.TEST, weight=0.6)

    players = []
    for i in range(0, 10):
      p = Player(name='Player ' + str(i))
      p.put()
      players.append(p)

    self.g1.players = [p.key for p in players]
    self.g1.put()

    self.g2.players = [p.key for p in players]
    self.g2.put()

    v = Vote(game=self.g1.key, three=players[7].key, two=players[9].key, one=players[3].key)
    v.put()
    v = Vote(game=self.g2.key, three=players[9].key, two=players[7].key, one=players[3].key)
    v.put()

  def testGameResults(self):
    results = game_results(self.g1)

    self.assertEqual('Player 7', results.three.get().name)
    self.assertEqual('Player 9', results.two.get().name)
    self.assertEqual('Player 3', results.one.get().name)
    self.assertEqual(1, results.voters)

    results = game_results(self.g2)
    self.assertEqual('Player 9', results.three.get().name)
    self.assertEqual('Player 7', results.two.get().name)
    self.assertEqual('Player 3', results.one.get().name)
    self.assertEqual(1, results.voters)

  def testOverallResults(self):
    results = overall_results(Team.TEST)

    # Overall rankings
    self.assertEqual('Player 9', results.player_votes[0].player.get().name)
    self.assertEqual('Player 7', results.player_votes[1].player.get().name)
    self.assertEqual('Player 3', results.player_votes[2].player.get().name)
    self.assertAlmostEqual(2.6, results.player_votes[0].total, places=3)
    self.assertAlmostEqual(2.4, results.player_votes[1].total, places=3)
    self.assertAlmostEqual(1.0, results.player_votes[2].total, places=3)

    # Game 1
    self.assertEqual('Player 7', results.game_votes[0].three.get().name)
    self.assertEqual('Player 9', results.game_votes[0].two.get().name)
    self.assertEqual('Player 3', results.game_votes[0].one.get().name)
    self.assertEqual(1, results.game_votes[0].voters)

    # Game 2
    self.assertEqual('Player 9', results.game_votes[1].three.get().name)
    self.assertEqual('Player 7', results.game_votes[1].two.get().name)
    self.assertEqual('Player 3', results.game_votes[1].one.get().name)
    self.assertEqual(1, results.game_votes[1].voters)

  def tearDown(self):
    self.testbed.deactivate()

if __name__ == '__main__':
  unittest.main()