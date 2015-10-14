from google.appengine.ext import db

class Player(db.Model):
  name = db.StringProperty(required=True)
  email = db.EmailProperty()
  photo = db.URLProperty()