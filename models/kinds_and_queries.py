
from google.appengine.ext import db
from google.appengine.api import memcache

from utilities.security import encrypt, decrypt # encrypts/decrypts keys to url-safe strings
from utilities.memcache import memcached # a decorator for memcache storage
import logging

# =========
# = Kinds =
# =========


class Student(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    level = db.StringProperty(required = True)
    date_joined = db.DateProperty(auto_now_add=True)
    # The classmethod 'register' is defined in authentication.py
    

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
We wrap queries and gets in a function which passes the appropriate key to be used for memcache.
"""

def StoryParent_key(update=False):
    """
    Gets the key of the lone StoryParent entity.
    
    Arguments:
        update: Boolean. If set to True, then it retrieves the key from the datastore and writes to memcache.
    
    Returns:
        The key of StoryParent.
        
    memcache keys stored:
        'StoryParent_key'
    """
    return _StoryParent_key(update=update)



def Student_by_id(student_id=None, update=False):
    """
    Gets a Student object given the student's id.
    
    Arguments:
        student_id: if s is a student, this corresponds to s.key().id()
        update: Boolean. Set to True to access datastore and overwrite memcache.
    
    Returns:
        a Student entity
        
    memcache keys stored:
        str(student_id) for each different student_id
    """
    if student_id:
        key = str(student_id)
        return _Student_by_id(memcache_key=key, update=update, student_id=student_id)

def Student_by_name(name=None, update=False):
    """
    Gets a Student given the student's username. Used mainly for authentication.
    
    Arguments:
        name: the name of the student (type: unicode)
        update: Boolean. Set to True to access datastore and overwrite memcache.
    
    Returns:
        a Student entity
        
    memcache keys stored:
        name for each different name given
    """
    if name:
        return _Student_by_name(memcache_key=name, update=update, name=name) 

def Student_by_key(student_key=None, update=False):
    """
    Gets a Student given the student's key.
    
    Arguments:
        student_key: the datastore key for the student (type: db.Key)
        update: Boolean. Set to True to access datastore and overwrite memcache.
    
    Returns:
        a Student entity
        
    memcache keys stored:
        str(student_key) for each different student_key given
    """
    if student_key:
        key = str(student_key)
        return _Student_by_key(memcache_key=key, update=update, student_key=student_key)
    



def Story_most_recent(difficulty="all", update=False):
    """
    Gets the 50 most recent stories of a given difficulty.
    
    Arguments:
        difficulty: 'all', 'Beginner', 'Intermediate', or 'Advanced'
        update: Boolean. Set to true if we want to retrieve from datastore and overwrite memcache.
    
    Returns:
        A list of at most 50 (story, uploader) tuples where the uploader is the Student who
        uploaded the given story.
    
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
    Gets at most 50 stories which have unanswered questions.
    
    Arguments:
        difficulty: 'all', 'Beginner', 'Intermediate', or 'Advanced'
        update: Boolean. Set to true if we want to retrieve from datastore and overwrite memcache.
    
    Returns:
        A list of at most 50 (story, uploader) tuples where the uploader is the Student who
        uploaded the given story. The stories may be in a random order.
        
    memcache_keys stored: 
    'unanswered all'
    'unanswered Beginner'
    'unanswered Intermediate'
    'unanswered Advanced'
    """
    key = "unanswered %s"%difficulty
    return _Story_unanswered(memcache_key=key, update=update, difficulty=difficulty)

def Story_by_id(story_id=None, update=False):
    """
    Gets a Story object given the story's id.
    
    Arguments:
        story_id: This corresponds to s.key().id() if s is a story.
        update: Boolean. Set to True to access datastore and overwrite memcache.
    
    Returns:
        a Story entity
    
    memcache keys stored:
        str(story_id) for each different story_id
    """
    if story_id:
        return _Story_by_id(memcache_key=str(story_id), update=update, story_id=story_id)



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

@memcached(memcache_key="StoryParent_key")
def _StoryParent_key():
    key = StoryParent.all(keys_only=True).get()
    if not key:
        key = StoryParent().put()
    return key



@memcached()
def _Student_by_key(student_key):
    return Student.get(student_key)

@memcached()
def _Student_by_id(student_id):
    return Student.get_by_id(student_id)

@memcached()
def _Student_by_name(name):
    return Student.all().filter('name =', name).get()



@memcached(memcache_key="most_recent all")
def _Story_most_recent(difficulty="all"):
    q = Story.all().ancestor(StoryParent_key()).order('-created')
    if difficulty != 'all':
        q.filter('difficulty =', difficulty)
        
    stories = [s for s in q.run(limit=50)]
    uploaders = [Student_by_key(Story.uploader.get_value_for_datastore(s)) for s in stories]
    
    return zip(stories, uploaders)

@memcached(memcache_key="unanswered all")
def _Story_unanswered(difficulty="all"):
    q = StoryExtras.all(keys_only=True).ancestor(StoryParent_key()).filter('has_unanswered_Q =', True).run(limit=50)
    story_keys = [s.parent() for s in q]
    stories = Story.get(story_keys) # stories is now a list of 50 random stories with unanswered Qs
    
    if difficulty != 'all':
        stories = filter(lambda s: s.difficulty == difficulty, stories)
    
    uploaders = [Student_by_key(Story.uploader.get_value_for_datastore(s)) for s in stories]
    return zip(stories, uploaders)

@memcached()
def _Story_by_id(story_id):
    return Story.get_by_id(story_id, parent=StoryParent_key())



