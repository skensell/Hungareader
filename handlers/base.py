from webapp2 import RequestHandler
import jinja2
import os

from utilities.security import make_secure_val, check_secure_val
from models.kinds_and_queries import Student

# Note that I needed an extra os.path.dirname to get to the Hungareader directory
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)


# ================
# = HANDLER BASE =
# ================


class HandlerBase(RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        #student is now always included
        self.write(self.render_str(template, student=self.student, **kw))
    
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.set_cookie(name, cookie_val) #path defaults to '/'
    
    def read_secure_cookie(self, name):
        "Returns the value of the cookie before the |."
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
    
    def login(self, student):
        self.set_secure_cookie('student_id', str(student.key().id()))
    
    def logout(self):
        self.response.delete_cookie('student_id')
    
    def initialize(self, *a, **kw): #runs on every request and checks if user is logged in
        RequestHandler.initialize(self, *a, **kw)
        sid = self.read_secure_cookie('student_id')
        # I should change this to Student_by_id
        self.student = sid and Student.by_id(int(sid))
    

