#framework stuff
import webapp2
import jinja2
import os, re, random

#for db storage and serialization
import json

#security and validation
from utilities.security import *
from utilities.youtube_api import *

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

from models.kinds_and_queries import *


# ============
# = HANDLERS =
# ============


class OneTimeUse(HandlerBase):
    def get(self):
        # code I want to execute once
        self.write("Success!")
    



# ===========
# = STORIES =
# ===========


class Stories(HandlerBase):
    def get(self):
        type_filter = self.request.get('type_filter') or 'most_recent'
        difficulty = self.request.get('difficulty') or 'all'
        
        stories_w_extras = recent_stories_w_extras(type_filter, difficulty);
        
        self.render('stories.html', stories_w_extras=stories_w_extras, type_filter=type_filter,
                    difficulty=difficulty)    
    

class AddStory(HandlerBase):
    def get(self):
        if not self.student:
            self.redirect("/login")
        else:
            self.render("addstory.html")
    
    def post(self):
        title = self.request.get('title').strip()
        summary = self.request.get('summary').strip()
        text = self.request.get('story').rstrip()
        video_url = self.request.get('video_url').strip()
        difficulty = self.request.get('difficulty')
        
        error_msg = "Please fill out all required fields."
        
        if not (title and summary and text):
            self.render("addstory.html", error=error_msg, title=title, summary=summary,
                        story=text, difficulty=difficulty, video_url=video_url )
        else:
            uploader = self.student
            video_id = get_video_id(video_url)
            s = Story(title=title, summary=summary, text=text,
                difficulty=difficulty, uploader=uploader, video_id=video_id)
            story_key = s.put()
            
            story_extras = StoryExtras(parent=story_key)
            story_extras.put()
            
            self.redirect("/%s"%story_key.id())
    

class ReadStory(HandlerBase):
    def get(self, story_id):
        story = Story.by_id(int(story_id))
        story_key = story.key()
        # logging.info([story.text])
        
        my_vocab = []
        if self.student:
            vl = VocabList.retrieve(self.student.key(), story_key)
            my_vocab = Vocab.words_and_keys(vl)
        
        v_lists = []
        for vl in VocabList.by_story(story_key):
            vocabs = Vocab.words_and_keys(vl)
            num_words = len(vocabs)
            v_lists.append((vl, num_words, vocabs))
        
        QandA = []
        for q in Question.by_story(story_key):
            q_key = q.key()
            q_key_e = encrypt(str(q_key))
            answers = [(a, encrypt(str(a.key()))) for a in Answer.by_question(q_key)]
            QandA.append((q, q_key_e, answers))
        
        story_extras = StoryExtras.by_story(story_key)
        
        self.render("readstory.html", story=story, my_vocab=my_vocab, v_lists=v_lists,
                    QandA=QandA, story_extras=story_extras)
    



# ======================
# = VOCAB MANIPULATION =
# ======================


class AddVocab(HandlerBase):
    def post(self):
        new_word = self.request.get("new_word").strip()
        new_def = self.request.get("new_def").strip()
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
    



# =========
# = Q & A =
# =========


class QandABase(HandlerBase):
    def post(self):
        self.story = Story.by_id(int(self.request.get('story_id')))
        self.s_extras = StoryExtras.by_story(self.story.key())
        
        self.action()
        
    def action(self):
        pass
    
    def update_unanswered(self, new_q=False):
        were_unanswered = self.s_extras.has_unanswered_Q
        unanswered_Qs = Question.unanswered(self.story.key())
        if new_q:
            self.s_extras.has_unanswered_Q = True
            self.s_extras.put()
        elif were_unanswered and not unanswered_Qs:
            self.s_extras.has_unanswered_Q = False
            self.s_extras.put()
        elif not were_unanswered and unanswered_Qs:
            self.s_extras.has_unanswered_Q = True
            self.s_extras.put()
    

class AskQuestion(QandABase):
    def action(self):
        question = self.request.get('question').strip()
        
        q = Question(parent=self.story, question=question, uploader=self.student)
        q.put()
        q_key_e = encrypt(str(q.key()))
        
        self.update_unanswered(new_q=True)
        
        self.render('readstoryQandA.html', question=q, q_key_e=q_key_e)
    

class DeleteQuestion(QandABase):
    def action(self):
        q_key_e = self.request.get('q_key_e')
        q_key = db.Key(decrypt(q_key_e))
        a_keys = Answer.get_all_keys(q_key)
        db.delete(a_keys)
        db.delete(q_key)
        
        self.update_unanswered()
    

class AnswerQuestion(QandABase):
    def action(self):
        q_key_e = self.request.get('q_key_e')
        q_key = db.Key(decrypt(q_key_e))
        answer = self.request.get('answer').strip()
        
        a = Answer(parent=q_key, answer=answer, uploader=self.student)
        a.put()
        
        self.update_unanswered()
        
        self.render('readstoryQandA.html', answers=[(a, encrypt(str(a.key())))])
    

class DeleteAnswer(QandABase):
    def action(self):
        a_key = db.Key(decrypt(self.request.get('a_key_e')))
        
        db.delete(a_key)
        
        self.update_unanswered()
    

class IncrementThanks(QandABase):
    def post(self):
        a_key_e = self.request.get('a_key_e')
        a_key = db.Key(decrypt(a_key_e))
        a = db.get(a_key)
        a.thanks += 1
        a.put()
    



# ============
# = Comments =
# ============


class SaveComments(HandlerBase):
    def post(self):
        story = Story.by_id(int(self.request.get('story_id')))
        s_extras = StoryExtras.by_story(story.key())
        comments = self.request.get('comments_text').strip()
        
        s_extras.comments = comments
        s_extras.put()
    



# ===========
# = MY DESK =
# ===========

class MyDeskBase(HandlerBase):
    def initialize(self, *a, **kw):
        HandlerBase.initialize(self, *a, **kw)
        self.v_lists = self.student and [vl for vl in VocabList.by_student(self.student.key()) if vl.vocab_list]
        self.stories = self.student and [(vl.story, encrypt(str(vl.story.key()))) for vl in self.v_lists]
    

class MyDesk(MyDeskBase):
    def get(self):
        if not self.student: 
            self.redirect('/login')
        else:
            self.render("mydesk.html", stories=self.stories)
    
    def post(self):
        num_words = self.request.get('num_words')
        if num_words != 'all':
            num_words = int(num_words)
        random_or_not = self.request.get('random_or_not')
        which_stories_e = self.request.get_all('which_stories')
        which_stories = map(db.Key, map(decrypt, which_stories_e))
        
        words = []
        for vl in self.v_lists:
            if vl.story.key() in which_stories:
                words += Vocab.words_and_keys(vl)
        
        if random_or_not == 'random':
            words = random.sample(words, min(num_words, len(words)))
        else:
            if num_words != 'all':
                words = words[:num_words]
        
        self.render("mydesk.html", stories=self.stories, my_vocab=words,
                    which_stories_e=which_stories_e, num_words=str(num_words),
                    random_or_not=random_or_not)        
    



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
                               ('/answerquestion/?', AnswerQuestion),
                               ('/askquestion/?', AskQuestion),
                               ('/deleteanswer/?', DeleteAnswer),
                               ('/deletequestion/?', DeleteQuestion),
                               ('/deletevocab/?', DeleteVocab),
                               ('/importvocab/?', ImportVocab),
                               ('/incrementthanks/?', IncrementThanks),
                               ('/login/?', Login),
                               ('/logout/?', LogOut),
                               ('/mydesk/?', MyDesk),
                               ('/onetimeuse/?', OneTimeUse),
                               ('/reordervocab/?', ReorderVocab),
                               ('/(\d+)', ReadStory),
                               ('/savecomments/?', SaveComments),
                               ('/signup/?', SignUp)
                              ],
                              debug=True)
