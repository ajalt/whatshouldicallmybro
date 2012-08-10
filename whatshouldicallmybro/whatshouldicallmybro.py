import webapp2
import random
import jinja2
import os
import json

with open('names.json') as namefile:
    names =  json.load(namefile) + ['BRObama', 'BRObadiah', 'BROmaha', "you look BROverworked", 'BROtini',
                                    'BROzilla', 'BROtylicious', 'BROmageddon', 'BROprah Winfrey',
                                    'Angelina BROlie', "Shaquille BRO'Neal", 'RonaldinBRO', 'BROhammad Ali' ]

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'name':random.choice(names)
        }
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage)],
                              debug=True)