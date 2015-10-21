import os
import jinja2
import logging
import webapp2

from models.game import Team

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
jinja_environment.filters['teamString'] = Team.getString

class MenuHandler(webapp2.RequestHandler):
  def get(self):
    teams = Team.getAll()
    template = jinja_environment.get_template("templates/results_menu.html")
    self.response.out.write(template.render({'teams': teams}))


app = webapp2.WSGIApplication([
  ('/results', MenuHandler)
], debug=True)
