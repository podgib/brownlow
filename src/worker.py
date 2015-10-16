import base64
import logging
import jinja2
import webapp2
import os

from google.appengine.api import taskqueue
from google.appengine.api import mail

from models.player import Player
from models.game import Game
from models.game import Team
from models.token import Token
from models.vote import SelfVote

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class SelfVoteHandler(webapp2.RequestHandler):
  def post(self):
    token_string = self.request.get('token')
    num_votes = self.request.get('votes')

    token = Token.all().filter("value =", token_string).get()
    if not token:
      return

    game = token.game
    voter = token.voter
    num_votes = self.request.get("votes")
    if num_votes == "1":
      votes_text = "1 vote"
    else:
      votes_text = num_votes + " votes"

    template = jinja_environment.get_template('templates/self_vote_email.txt')
    if game.team == Team.WOMEN:
      pronoun = 'herself'
    else:
      pronoun = 'himself'

    subject = "OUARFC: " + voter.name + " tried to give " + pronoun + " " + votes_text

    message = mail.EmailMessage(sender="OUARFC <no-reply@ouarfc-vote.appspotmail.com>", subject=subject)
    message.to = "pascoeg@gmail.com"
    message.body = template.render(
      {'name': voter.name, 'opponent': game.opponent, 'date': game.date, 'pronoun': pronoun, 'votes': votes_text})
    message.send()
    logging.info(message.body)

    vote = SelfVote(game=game, voter=voter)
    vote.put()

class EmailHandler(webapp2.RequestHandler):
  def post(self):
    player_id = self.request.get('player')
    game_id = self.request.get('game')

    player = Player.get_by_id(int(player_id))
    game = Game.get_by_id(int(game_id))

    token_string = base64.urlsafe_b64encode(os.urandom(32))
    token = Token(value=token_string, voter=player, game=game, used=False)
    token.put()

    url = "http://vote.ouarfc.co.uk/vote/" + token_string

    template = jinja_environment.get_template('templates/email.txt')
    subject = "OUARFC: Please Vote For Best & Fairest"
    message = mail.EmailMessage(sender="OUARFC <no-reply@ouarfc-vote.appspotmail.com>", subject=subject)
    message.to = player.email
    message.body = template.render(
      {'name':player.name, 'opponent':game.opponent, 'date':game.date, 'team': Team.getString(game.team), 'url':url})
    logging.info("Sending email to " + player.email)
    message.send()
    logging.info(message.body)

app = webapp2.WSGIApplication(
  [ ('/worker/email', EmailHandler),
    ('/worker/self_vote', SelfVoteHandler)], debug=True)
