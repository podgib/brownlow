import webapp2
import os
import jinja2

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class VoteHandler(webapp2.RequestHandler):
  def get(self):
   self.response.out.write("Hello")

class SubmitHandler(webapp2.RequestHandler):
  def post(self):
    self.response.out.write("Submitted")

app = webapp2.WSGIApplication([
    webapp2.Route('/vote/<token>', handler=VoteHandler),
    webapp2.Route('/vote', handler=SubmitHandler),
], debug=True)
