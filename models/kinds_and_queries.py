
from google.appengine.ext import db
from google.appengine.api import memcache

from utilities.security import encrypt, decrypt # encrypts/decrypts keys to url-safe strings
from utilities.memcache import memcached # a decorator for memcache storage
import logging

# =========
# = Kinds =
# =========


class Student(db.Model):
    """It also has the classmethod 'register' defined in authentication.py """
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    level = db.StringProperty(required = True)
    date_joined = db.DateProperty(auto_now_add=True)
    
    @classmethod
    def by_id(cls, sid):
        return Student.get_by_id(sid)
    
    @classmethod
    def by_name(cls, name):
        return Student.all().filter('name =', name).get()
    

class StoryParent(db.Model):
    # The parent of every Story
    # needed for consistency (which requires ancestor queries)
    exists = db.BooleanProperty(default=True)

class Story(db.Model):
    # always has parent = StoryParent (of which there is only 1)
    title = db.StringProperty(required = True)
    author = db.StringProperty(default="Unknown")
    summary = db.StringProperty(required = True) #must be < 500 characters
    text = db.TextProperty(required = True)
    video_id = db.StringProperty()
    tags = db.ListProperty(unicode)
    difficulty = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    uploader = db.ReferenceProperty(Student)
    
    @classmethod
    def most_recent(cls, difficulty="all"):
        q = Story.all().ancestor(StoryParent_key()).order('-created')
        if difficulty != 'all':
            q.filter('difficulty =', difficulty)
        return q
    
    @classmethod
    def by_id(cls, sid):
        # Now that each story has a parent, the parent kw is necessary
        return Story.get_by_id(sid, parent=StoryParent_key())
    
    @classmethod
    def key_from_id(cls, sid):
        # I should delete this function if nothing is using it.
        return Story.get_by_id(sid, parent=StoryParent_key()).key()
    

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
        """Takes a vocab_list object and returns a list of tuples (v, v_key_e) where
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
    
    @classmethod
    def by_student(cls, student_key):
        return VocabList.all().filter("student =", student_key).order('-created').run(limit=100)
    

class Answer(db.Model):
    # always has a question as its parent
    answer = db.TextProperty(required=True)
    uploader = db.ReferenceProperty(Student)
    thanks = db.IntegerProperty(default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def by_question(cls, q_key):
        return Answer.all().ancestor(q_key).order('created').run(limit=10)
    
    @classmethod
    def one(cls, q_key):
        return Answer.all().ancestor(q_key).get()
        
    @classmethod
    def get_all_keys(cls, q_key):
        return [a for a in Answer.all().ancestor(q_key).run(keys_only=True)]
    

class Question(db.Model):
    # always has a story as its parent
    question = db.TextProperty(required=True)
    uploader = db.ReferenceProperty(Student)
    created = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def by_story(cls, story_key):
        return Question.all().ancestor(story_key).order('-created').run(limit=100)
    
    @classmethod
    def unanswered(cls, story_key):
        """returns the unanswered Questions of a given story"""
        Q = []
        for q in Question.by_story(story_key):
            if not Answer.one(q.key()):
                Q.append(q)
        return Q
    

class StoryExtras(db.Model):
    """Contains properties of a given story which change frequently."""
    # always has a parent Story
    comments = db.TextProperty(default="Delete me. Write all over me. This is just a wall.")
    has_unanswered_Q = db.BooleanProperty(default=False)
    
    @classmethod
    def by_story(cls, story_key):
        return StoryExtras.all().ancestor(story_key).get()
    





# ===========
# = Queries =
# ===========
"""
Sometimes a query may want to have several keys in memcache (e.g. 'most_recent all' 
and 'most_recent advanced'). If so, we wrap the query in a function which passes the appropriate key
to be used for memcache.
"""

def Student_by_id():
    pass

def Student_by_name():
    pass



@memcached(memcache_key="StoryParent_key")
def StoryParent_key():
    """returns the key for the StoryParent model which serves as the parent to every Story.
    If the StoryParent hasn't been created yet, it creates it.
    """
    key = StoryParent.all(keys_only=True).get()
    if not key:
        key = StoryParent().put()
    return key




def Story_most_recent(difficulty="all", update=False):
    """
    returns a list of the 50 most recent Storys of a given difficulty (from memcache if possible).
    If update=True then it returns from the datastore and writes to memcache.
    
    memcache_keys stored: 
    'most_recent all'
    'most_recent Beginner'
    'most_recent Intermediate'
    'most_recent Advanced'
    """
    key = "most_recent %s"%difficulty
    return _Story_most_recent(memcache_key=key, update=update, difficulty=difficulty)

def Story_unanswered(difficulty="all", update=False):
    """
    returns a list of 50 most random Storys which have unanswered questions
    (from memcache if possible). If update=True then it returns from the datastore and writes to memcache.
    
    memcache_keys stored: 
    'unanswered all'
    'unanswered Beginner'
    'unanswered Intermediate'
    'unanswered Advanced'
    """
    key = "unanswered %s"%difficulty
    return _Story_unanswered(memcache_key=key, update=update, difficulty=difficulty)


def StoryExtras_by_story():
    pass










def Question_by_story():
    pass

def Question_unanswered():
    pass

def Answer_by_question():
    pass

def Answer_one():
    pass

def Answer_get_all_keys():
    pass



# =====================
# = Unwrapped Queries =
# =====================

@memcached(memcache_key="most_recent all")
def _Story_most_recent(difficulty="all"):
    q = Story.most_recent(difficulty)
    return [s for s in q.run(limit=50)]

@memcached(memcache_key="unanswered all")
def _Story_unanswered(difficulty="all"):
    """Returns a list of <= 50 stories with unanswered Qs.
    Note that adding the ancestor filter is necessary for consistency."""
    
    q = StoryExtras.all(keys_only=True).ancestor(StoryParent_key()).filter('has_unanswered_Q =', True).run(limit=50)
    story_keys = [s.parent() for s in q]
    stories = Story.get(story_keys) #stories is now a list of 50 random stories with unanswered Qs
    if difficulty != 'all':
        stories = filter(lambda s: s.difficulty == difficulty, stories)
    return stories




# old queries

def recent_stories_w_extras(type_filter='most_recent', difficulty='all', update=False):
    """
    The main query called by Stories. Looks in memcache first unless update=True.
    
    returns: [(story, story_extras) for story satisfying filters]
    """
    key = 'type_filter:%s difficulty:%s'% (type_filter, difficulty)
    
    S = []
    
    stories_q = Story.most_recent()
    
    if difficulty != 'all':
        stories_q.filter('difficulty =', difficulty)
    
    for s in stories_q.run(limit=50):
        s_extras = StoryExtras.by_story(s.key())
    
        if type_filter == 'most_recent':
            S.append((s,s_extras))
        elif type_filter == 'unanswered':
            if s_extras.has_unanswered_Q:
                S.append((s,s_extras))
            
    return S
