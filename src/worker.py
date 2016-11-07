import base64
import logging
import jinja2
import webapp2
import os
import urllib
import json

from google.appengine.api import taskqueue
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models.player import Player
from models.game import Game
from models.game import Team
from models.token import Token
from models.vote import SelfVote
import config

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class SelfVoteHandler(webapp2.RequestHandler):
  def post(self):
    token_string = self.request.get('token')
    num_votes = self.request.get('votes')

    token = Token.query(Token.value == token_string).get()
    if not token:
      return

    game = token.game.get()
    voter = token.voter.get()
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

    message = mail.EmailMessage(sender="OUARFC <vote@ouarfc-vote.appspotmail.com>", subject=subject)
    message.to = "pascoeg@gmail.com"
    message.body = template.render(
      {'name': voter.name, 'opponent': game.opponent, 'date': game.date, 'pronoun': pronoun, 'votes': votes_text})
    message.send()
    logging.info(message.body)

    vote = SelfVote(game=game.key, voter=voter.key)
    vote.put()

class EmailHandler(webapp2.RequestHandler):
  def post(self):
    player_id = self.request.get('player')
    game_id = self.request.get('game')

    player = Player.get_by_id(int(player_id))
    game = Game.get_by_id(int(game_id))

    token = Token.query(ndb.AND(Token.game == game.key, Token.voter == player.key)).get()
    reminder = False

    if not token:
      logging.info("No token found for %s. Creating new token.", player.name)
      token_string = base64.urlsafe_b64encode(os.urandom(16))[:-2]
      token = Token(value=token_string, voter=player.key, game=game.key, used=False)
      token.put()
    else:
      logging.info("Token found for %s.", player.name)
      reminder = True
      if token.used:
        logging.info("%s has already voted, not sending email.", player.name)
        return

    url = "http://vote.ouarfc.co.uk/vote/" + token.value

    if player.phone and not reminder:
      logging.info('Sending SMS to %s', player.name)
      template = jinja_environment.get_template('templates/sms.txt')
      sms_data = {
        'ORIGINATOR':'OUARFC',
        'NUMBERS':player.phone,
        'BODY':template.render({'url':url, 'opponent':game.opponent, 'team':Team.getString(game.team)})
      }

      response = urlfetch.fetch('https://api.zensend.io/v3/sendsms', payload=urllib.urlencode(sms_data),
                                method=urlfetch.POST, headers={"X-API-KEY": config.zensend_key})
      content_type = response.headers['content-type']
      if content_type is not None and "application/json" in content_type:
        result = json.loads(response.content)
        if "success" in result:
          logging.info("Successfully sent SMS to " + player.phone)
          if config.phone_only:
            # SMS was a success, don't send email
            return
        elif "failure" in result:
          failure = result["failure"]
          logging.error("SMS send failed. Player: %s, phone: %s, parameter: %s, error code: %s, status code: %s",
                        player.name, player.phone, failure["parameter"], failure["failcode"], response.status_code)
        else:
          logging.error("SMS send failed. Status code: %s", response.status_code)
      else:
        logging.error("SMS send failed. Status code: %s", response.status_code)

    template = jinja_environment.get_template('templates/email.txt')
    subject = "OUARFC: Please Vote For Best & Fairest"
    if reminder:
      subject = "Reminder - " + subject
    message = mail.EmailMessage(sender="OUARFC <vote@ouarfc-vote.appspotmail.com>", subject=subject)
    message.to = player.email
    message.body = template.render(
        {'name':player.name, 'opponent':game.opponent, 'date':game.date, 'team': Team.getString(game.team), 'url':url})
    logging.info("Sending email to " + player.email)
    message.send()
    logging.info(message.body)


app = webapp2.WSGIApplication(
  [ ('/worker/email', EmailHandler),
    ('/worker/self_vote', SelfVoteHandler)], debug=True)
