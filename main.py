#framework stuff
import webapp2
import jinja2
import os, re

#for db storage and serialization
import json

#security and validation
from utilities.security import *

#for debugging
import logging


from google.appengine.ext import db
from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)




# ================
# = HANDLER BASE =
# ================

class HandlerBase(webapp2.RequestHandler):
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
        webapp2.RequestHandler.initialize(self, *a, **kw)
        sid = self.read_secure_cookie('student_id')
        self.student = sid and Student.by_id(int(sid))
    


# ===================
# = DATASTORE KINDS =
# ===================


class Student(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    level = db.StringProperty(required = True)
    date_joined = db.DateProperty(auto_now_add=True)
    vocab_added = db.IntegerProperty()
    vocab_increase = db.IntegerProperty()
    vocab_reviews = db.IntegerProperty()
    stories_read = db.IntegerProperty()
    stories_uploaded = db.IntegerProperty()#can get from references from Story
    
    @classmethod
    def by_id(cls, sid):
        return Student.get_by_id(sid)
    
    @classmethod
    def by_name(cls, name):
        return Student.all().filter('name =', name).get()
    
    @classmethod
    def register(cls, name, pw, level, email = None):
        pw_hash = make_pw_hash(name, pw)
        return Student(name = name,
                    pw_hash = pw_hash,
                    level = level,
                    email = email)
    

class Story(db.Model):
    title = db.StringProperty(required = True)
    summary = db.StringProperty() #must be < 500 characters
    text = db.TextProperty(required = True)
    difficulty = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    uploader = db.ReferenceProperty(Student)
    
    
    @classmethod
    def most_recent(cls):
        return Story.all().order('-created').run(limit=10)
    
    @classmethod
    def by_id(cls, sid):
        return Story.get_by_id(sid)
    
    @classmethod
    def key_from_id(cls, sid):
        return Story.get_by_id(sid).key()
    

class Vocab(db.Model):
    hungarian = db.StringProperty(required = True)
    meaning = db.StringProperty(required = True)
    
    @classmethod
    def by_id(cls, vid):
        return Vocab.get_by_id(vid)
    
    @classmethod
    def retrieve(cls, hungarian, meaning):
        return Vocab.all().filter("hungarian =", hungarian).filter("meaning =", meaning).get()
    
    @classmethod
    def words_and_keys(cls, vocab_list):
        """Takes a vocab_list of keys and returns a list of tuples (v, v_key_e) where
        v is the vocab instance and v_key_e is the encrypted key for that instance."""
        if not vocab_list:
            return []
        v_list = Vocab.get(vocab_list.vocab_list) # a list of instances
        return [(v, encrypt(str(v_key))) for (v,v_key) in zip(v_list, vocab_list.vocab_list)]
    

class VocabList(db.Model):
    student = db.ReferenceProperty(Student)
    story = db.ReferenceProperty(Story)
    vocab_list = db.ListProperty(db.Key) #a list of vocab_words
    created = db.DateTimeProperty(auto_now_add = True)
    
    #I could check the site below for reducing .get() methods
    #http://stackoverflow.com/questions/4719700/list-of-references-in-google-app-engine-for-python/4730415#4730415
    @classmethod
    def retrieve(cls, student_key, story_key):
        #note that the student= is no good.  The SPACE IS NECESSARY.
        return VocabList.all().filter("student =", student_key).filter("story =", story_key).get()
    
    @classmethod
    def by_story(cls, story_key):
        # order this by created
        return VocabList.all().filter("story =", story_key).run(limit=10)
    


# ============
# = HANDLERS =
# ============

# ===========
# = STORIES =
# ===========

# Note: There are keys-only queries I could be implementing.

class Stories(HandlerBase):
    def get(self):
        most_recent = Story.most_recent()
        self.render('stories.html', most_recent=most_recent)    
    

class AddStory(HandlerBase):
    def get(self):
        if not self.student:
            self.redirect("/login")
        else:
            self.render("addstory.html")
    
    def post(self):
        title = self.request.get('title')
        summary = self.request.get('summary')
        text = self.request.get('story')
        difficulty = self.request.get('difficulty')
        
        error_msg = "Title, story, and difficulty are all required fields."
        
        if not (title and summary and text):
            self.render("addstory.html", error=error_msg, title=title, summary=summary,
                        story=text, difficulty=difficulty)
        else:
            uploader = self.student
            s = Story(title=title, summary=summary, text=text,
                difficulty=difficulty, uploader=uploader)
            s.put()
            self.redirect("/")
    

class ReadStory(HandlerBase):
    def get(self, story_id):
        story = Story.by_id(int(story_id))
        story_key = story.key()
        
        my_vocab = []
        if self.student:
            vl = VocabList.retrieve(self.student.key(), story_key)
            my_vocab = Vocab.words_and_keys(vl)
        
        v_lists = []
        for vl in VocabList.by_story(story_key):
            vocabs = Vocab.words_and_keys(vl)
            num_words = len(vocabs)
            v_lists.append((vl, num_words, vocabs))
        
        self.render("readstory.html", story=story, my_vocab=my_vocab, v_lists=v_lists)
    


# ======================
# = VOCAB MANIPULATION =
# ======================

class AddVocab(HandlerBase):
    def post(self):
        new_word = self.request.get("new_word")
        new_def = self.request.get("new_def")
        mode = self.request.get("mode")
        
        # retrieve the word from db or create it
        v = Vocab.retrieve(new_word, new_def)
        if not v:
            v = Vocab(hungarian=new_word, meaning=new_def)
            v.put()
        v_key = v.key()
        
        # add the word to the vocab list
        # these 4 lines can be abstracted out
        story = Story.by_id(int(self.request.get('story_id')))
        vl = VocabList.retrieve(self.student.key(), story.key())
        if not vl:
            vl = VocabList(student=self.student, story=story)
            
        if mode == 'normal':
            vl.vocab_list.append(v_key)
        elif mode == 'edit':
            vl_index = int(self.request.get('vl_index'))
            vl.vocab_list[vl_index] = v_key
        vl.put()
        
        # return the new row
        new_row = u'<tr id="{}"><td>{}</td><td>{}</td></tr>'.format(encrypt(str(v_key)), new_word, new_def)
        self.response.write(new_row)
    

class DeleteVocab(HandlerBase):
    def post(self):
        story = Story.by_id(int(self.request.get('story_id')))
        vl = VocabList.retrieve(self.student.key(), story.key())
        
        vl_indices = map(int,self.request.POST.getall('vl_indices[]'))
        vl.vocab_list[:] = [v for (i,v) in enumerate(vl.vocab_list) if i not in vl_indices]
        vl.put()
    

class ImportVocab(HandlerBase):
    def post(self):
        story = Story.by_id(int(self.request.get('story_id')))
        
        vl = VocabList.retrieve(self.student.key(), story.key())
        if not vl:
            vl = VocabList(student=self.student, story=story)
            
        keys_to_add_e = self.request.POST.getall('keys[]')
        keys_to_add = map(db.Key, map(decrypt, keys_to_add_e))
        
        vl.vocab_list.extend(keys_to_add)
        vl.put()
    

class ReorderVocab(HandlerBase):
    def post(self):
        story = Story.by_id(int(self.request.get('story_id')))
        vl = VocabList.retrieve(self.student.key(), story.key())
        
        keys_e = self.request.POST.getall('keys[]')
        keys = map(db.Key, map(decrypt, keys_e))
        
        vl.vocab_list = keys
        vl.put()



# ===========
# = MY DESK =
# ===========

class MyDesk(HandlerBase):
    def get(self):
        if not self.student: 
            self.redirect('/login')
        else:
            self.render("mydesk.html")


# =========================
# = LOGIN, LOGOUT, SIGNUP =
# =========================

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
    




##### URL-HANDLER MAPPING
app = webapp2.WSGIApplication([
                               ('/?', Stories),
                               ('/addstory/?', AddStory),
                               ('/addvocab/?', AddVocab),
                               ('/deletevocab/?', DeleteVocab),
                               ('/importvocab/?', ImportVocab),
                               ('/login/?', Login),
                               ('/logout/?', LogOut),
                               ('/mydesk/?', MyDesk),
                               ('/reordervocab/?', ReorderVocab),
                               ('/(\d+)', ReadStory),
                               ('/signup/?', SignUp)
                              ],
                              debug=True)
