from google.appengine.ext import ndb

class Player(ndb.Model):
  name = ndb.StringProperty(required=True)
  email = ndb.StringProperty()
  phone = ndb.StringProperty()
