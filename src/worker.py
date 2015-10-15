import base64
import logging
import jinja2
import webapp2
import os

from google.appengine.api import taskqueue
from google.appengine.api import mail

from models.player import Player
from models.game import Game
from models.token import Token

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


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
    message.body = template.render({'name':player.name, 'opponent':game.opponent, 'date':game.date, 'url':url})
    logging.info(message.body)
    logging.info("Sending email to " + player.email)
    message.send()

app = webapp2.WSGIApplication(
  [ ('/worker/email', EmailHandler)], debug=True)
