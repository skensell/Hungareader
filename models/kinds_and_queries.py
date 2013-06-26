
from google.appengine.ext import db
from google.appengine.api import memcache

from utilities.security import encrypt, decrypt


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
    

class Story(db.Model):
    title = db.StringProperty(required = True)
    summary = db.StringProperty(required = True) #must be < 500 characters
    text = db.TextProperty(required = True)
    video_id = db.StringProperty()
    difficulty = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    uploader = db.ReferenceProperty(Student)
    
    @classmethod
    def most_recent(cls):
        return Story.all().order('-created')
    
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
    # always has a parent Story
    comments = db.TextProperty(default="Delete me. Write all over me. This is just a wall.")
    has_unanswered_Q = db.BooleanProperty()
    
    @classmethod
    def by_story(cls, story_key):
        return StoryExtras.all().ancestor(story_key).get()
    





# ===========
# = Queries =
# ===========


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
