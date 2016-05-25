from google.appengine.ext import ndb

class Season(ndb.Model):
  public_round = ndb.IntegerProperty(repeated=True)
