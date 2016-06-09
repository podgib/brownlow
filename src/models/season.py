from google.appengine.ext import ndb
from game import Team

class Season(ndb.Model):
  public_round = ndb.IntegerProperty(repeated=True)

  def get_public_round(self, team_name):
    team = Team.getTeam(team_name)
    if team < 0:
      index = 2
    else:
      index = team - 1
    return self.public_round[index]
