from base import HandlerBase

from models.kinds_and_queries import Student
import re, hashlib, random, string

class Login(HandlerBase):
    def get(self):
        self.render("login.html")
    
    def post(self):
        name = self.request.get('username')
        pw = self.request.get('password')
        s = Student.by_name(name)
        if not s:
            self.render("login.html", error_username='That username does not exist.')
        else:
            if not pw_matches(name, pw, s.pw_hash):
                self.render("login.html", error_password="Invalid password.")
            else:#success
                self.login(s)
                self.redirect('/')
    

class LogOut(HandlerBase):
    def get(self):
        self.logout()
        self.redirect('/login')
    

class SignUp(HandlerBase):
    def get(self):
        self.render("signup.html")
    
    def post(self):
        new_user = self.request.get('new_user')
        new_pwd = self.request.get('new_pwd')
        verify = self.request.get('verify')
        level = self.request.get('level')
        email = self.request.get('email')
        
        have_error, template_params = validate(new_user, new_pwd, verify, level, email)
        #validate() checks regexps and level, now we check if username is taken
        if Student.by_name(new_user):
               template_params['error_new_user'] = "That username is already taken."
               have_error = True
        
        if have_error:
            self.render("signup.html", **template_params)
        else:
            s = Student.register(new_user, new_pwd, level, email)
            s.put() #puts s in datastore
            self.login(s) #sets the cookie
            self.redirect('/')
    



# ================
# = REGISTRATION =
# ================

def register(cls, name, pw, level, email = None):
    """This will be a class method of Student."""
    pw_hash = make_pw_hash(name, pw)
    return Student(name = name,
                pw_hash = pw_hash,
                level = level,
                email = email)

Student.register = classmethod(register)

# ===========================
# = SECURE PASSWORDS =
# ===========================

def make_salt():
   return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s'%(salt,h)

def pw_matches(name, pw, h): #replaces valid_pw from CS253
    """True if name and pw hash to get h(the pw_hash on file)."""
    salt = h.split(',')[0]
    return h == make_pw_hash(name, pw, salt=salt)




# ===================================
# = VALID USERNAMES, PWDS, & EMAILS =
# ===================================

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

def validate(new_user, new_pwd, verify, level, email):
    """SignUp form validation."""
    
    have_error=False
    t_params = dict(new_user=new_user, email=email) #template parameters
    if not valid_username(new_user):
        t_params['error_new_user'] = "That's not a valid username."
        have_error = True
    
    if not valid_password(new_pwd):
        t_params['error_new_pwd'] = "That's not a valid password."
        have_error = True
    elif new_pwd != verify:
        t_params['error_verify'] = "Your passwords don't match."
        have_error = True
    
    if not valid_email(email):
        t_params['error_email'] = "That's not a valid email."
        have_error = True
    
    if level.lower() not in ['beginner', 'intermediate', 'advanced']:
        t_params['error_level'] = 'Please indicate your current level of Hungarian'
        have_error = True
    
    return have_error, t_params



