import webapp2
import os
import jinja2

from models.player import Player

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class AddPlayerHandler(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template("templates/add_player.html")
    self.response.out.write(template.render({}))

  def post(self):
    name = self.request.get("name")
    if not name:
      self.response.out.write("Error: must supply a name")
      return
    if Player.all().filter("name =", name).count() > 0:
      self.response.out.write("A player with that name already exists")
      return

    player = Player(name=name)
    player.put()

    self.response.out.write("Successfully added " + name)

app = webapp2.WSGIApplication([
  webapp2.Route('/admin/add_player', handler=AddPlayerHandler),
], debug=True)
