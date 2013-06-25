
import unittest
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed

from functools import update_wrapper




class Student(db.Model):
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
    difficulty = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    
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
    



class memcached(object):
    """
    This is a decorator for storing query results in memcache.
    
    @memcached(key='some_query')
    def q():
        return [s for s in Story.all().run()]
    
    r = q(key='my_favorite_key', arg1, arg2, ...)
    
    Each time a new key is given to q it hits the datastore, stores it in memcache, and returns it.
    Each time an old key is given it hits the memcache and returns it, unless update=True, in which
    case it hits the datastore, stores it in memcache, and returns it.
    If q is called with no "key" argument, the default key of "some_query" will be used.
    
    @memcached() can also be called without any arguments, providing a default key of DEFAULT_KEY
    but this is not recommended.
    
    """
    def __init__(self, key="some_key", *args, **kw):
        self.key = key or 'DEFAULT_KEY'
    
    def __call__(self, f):
        """This is called just once when we use @memcached()"""
        def memoized_f(key=self.key, update=False, *args, **kw):
            client = memcache.Client()
            val = client.gets(key)
            if val != None and not update:
                #logging.info('Already in memcache, returning.')
                return val
            else:
                #logging.info("Computing the result.")   
                result = f(*args,**kw) # hits the datastore
                if val is None: # add it for the first itme
                    client.add(key, result)
                    return result
                else:
                    # update=True
                    #
                    # avoid race conditions which may happen if multiple people
                    # try to update at the same time
                    for i in xrange(5):
                        if client.cas(key, result):
                            #logging.info("Setting memcache value and i equals %d"%i)
                            return result
                        client.gets(key)
        
        return update_wrapper(memoized_f, f)
    



class TestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
    
    def tearDown(self):
        self.testbed.deactivate()
    
    #
    # Everything above is config.  Below I define tests.
    #
    def testMemcacheDecorator1(self):
        """Tests basic functionality of Memcache Decorator."""
        Story(title="Harry Potter", difficulty="Intermediate").put()
        Story(title="A korhazban", difficulty="Beginner").put()
        
        @memcached(key="most_recent_stories")
        def most_recent_stories():
            return [s for s in Story.most_recent().run(limit=10)]
        
        stories = most_recent_stories() # miss 1, sets with default key
        
        self.assertEqual(["A korhazban", "Harry Potter"], [s.title for s in stories])
        self.assertEqual(2, len(stories))
        retrieved_stories = memcache.get('most_recent_stories') # hit 1
        self.assertEqual(2, len(retrieved_stories))
        self.assertEqual([stories[i].title for i in xrange(2)], [retrieved_stories[i].title for i in xrange(2)])
        self.assertEqual([stories[i].difficulty for i in xrange(2)],
                        [retrieved_stories[i].difficulty for i in xrange(2)])
        
        for i in xrange(3):
            stories = most_recent_stories() #hit 2, 3, 4
        
        stats = memcache.get_stats()
        self.assertEqual(4, stats['hits'] )
        self.assertEqual(1, stats['misses'])
        
        
        # trying out a new key
        Story(title="A new title", difficulty="Advanced").put()
        Story(title="Yet another story", difficulty="Beginner").put()
        
        stories2 = most_recent_stories(key="whatever I want") # miss 2, sets with new key
        retrieved_stories2 = memcache.get('whatever I want') # hit 5
        self.assertEqual(4, len(stories2))
        self.assertEqual(4, len(retrieved_stories2))
        
        stats = memcache.get_stats()
        stories3 = memcache.get('most_recent_stories') # hit 6
        self.assertEqual(2, len(stories3))
        self.assertEqual(2, stats['misses'])
        
        s4 = most_recent_stories(key="whatever I want") # hit 7
        self.assertEqual(4, len(s4))
        self.assertEqual(s4[0].title, "Yet another story")
        
        s5 = most_recent_stories(key="most_recent_stories", update=True) # hit 8
        s6 = memcache.get('most_recent_stories') # hit 9
        self.assertEqual(4, len(s5))
        self.assertEqual(4, len(s6))
        
        stats = memcache.get_stats()
        self.assertEqual(9, stats['hits'])
        self.assertEqual(2, stats['misses'])
    
    def testMemcacheDecorator2(self):
        """Tests what can be stored in memcache."""
        Story(title="Harry Potter", difficulty="Intermediate").put()
        Story(title="A korhazban", difficulty="Beginner").put()
        
        @memcached(key="most_recent_stories")
        def most_recent_stories():
            return Story.most_recent().run()
        
        self.assertRaises(Exception, most_recent_stories) # can't store query.run() in memcache
        
        @memcached(key="the most recent")
        def a_recent_story():
            return Story.most_recent().fetch(1) # works because this just fetches a list of at most 1
        
        s = a_recent_story()
        cached_s = memcache.get('the most recent')
        self.assertEqual(1, len(s))
        self.assertEqual('A korhazban', s[0].title)
        self.assertEqual(1, len(cached_s))
        
        @memcached(key="just a story")
        def just_a_story():
            return Story.most_recent().get()
        
        s = just_a_story()
        cached_s = memcache.get('just a story')
        self.assertEqual('A korhazban', s.title)
        self.assertEqual(s.title, cached_s.title)
        self.assertEqual(s.key(), cached_s.key())
        self.assertEqual(s.key().id(), cached_s.key().id())
    
    def testMemcacheDecorator3(self):
        """Tests whether the optional arguments will work in retrieve_stories."""
        pass
    




    



if __name__ == "__main__":
    unittest.main()
