
import unittest
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed

from utilities.memcache import memcached # the decorator being tested


# ===========
# = Testing =
# ===========


class Story(db.Model):
    title = db.StringProperty(required = True)
    difficulty = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    
    @classmethod
    def most_recent(cls, difficulty="all"):
        q = Story.all().order('-created')
        if difficulty != 'all':
            q.filter('difficulty =', difficulty)
        return q
    



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
        
        @memcached(memcache_key="most_recent_stories")
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
        
        stories2 = most_recent_stories(memcache_key="whatever I want") # miss 2, sets with new key
        retrieved_stories2 = memcache.get('whatever I want') # hit 5
        self.assertEqual(4, len(stories2))
        self.assertEqual(4, len(retrieved_stories2))
        
        stats = memcache.get_stats()
        stories3 = memcache.get('most_recent_stories') # hit 6
        self.assertEqual(2, len(stories3))
        self.assertEqual(2, stats['misses'])
        
        s4 = most_recent_stories(memcache_key="whatever I want") # hit 7
        self.assertEqual(4, len(s4))
        self.assertEqual(s4[0].title, "Yet another story")
        
        s5 = most_recent_stories(memcache_key="most_recent_stories", update=True) # hit 8
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
        
        @memcached(memcache_key="most_recent_stories")
        def most_recent_stories():
            return Story.most_recent().run()
        
        self.assertRaises(Exception, most_recent_stories) # can't store query.run() in memcache
        
        @memcached(memcache_key="the most recent")
        def a_recent_story():
            return Story.most_recent().fetch(1) # works because this just fetches a list of at most 1
        
        s = a_recent_story()
        cached_s = memcache.get('the most recent')
        self.assertEqual(1, len(s))
        self.assertEqual('A korhazban', s[0].title)
        self.assertEqual(1, len(cached_s))
        
        @memcached(memcache_key="just a story")
        def just_a_story():
            return Story.most_recent().get()
        
        s = just_a_story()
        cached_s = memcache.get('just a story')
        self.assertEqual('A korhazban', s.title)
        self.assertEqual(s.title, cached_s.title)
        self.assertEqual(s.key(), cached_s.key())
        self.assertEqual(s.key().id(), cached_s.key().id())
    
    def testMemcacheDecorator3(self):
        """Tests whether the @classmethod will work with the decorator. IT DOES NOT!"""
        class AStory(db.Model):
            title = db.StringProperty()
            difficulty = db.StringProperty()
        
            @classmethod
            @memcached(memcache_key="SOME_TITLE", class_method=True)
            def by_title(cls,title=''):
                return AStory.all().filter("title =", title).get()
        
        
        #AStory(title="winners", difficulty="Beginner").put()
        #AStory(title="losers", difficulty="Advanced").put()
        
        #Can it take filter arguments?
        # s1 = AStory.by_title(memcache_key="winners", title="winners") # miss 1 
        # cached_s1 = memcache.get("winners") # hit 1
        # self.assertEqual(s1.difficulty, cached_s1.difficulty)
        # self.assertEqual(s1.title, cached_s1.title)
        
    
    def testMemcacheDecorator4(self):
        """Tests whether the decorator works on a function with arguments."""
        Story(title="Harry Potter", difficulty="Intermediate").put()
        Story(title="A korhazban", difficulty="Beginner").put()
        
        @memcached(memcache_key="most_recent all")
        def Story_most_recent(difficulty='all'):
            q = Story.most_recent()
            if difficulty != "all":
                q = q.filter('difficulty =', difficulty)
            return q.get()
        
        s1 = Story_most_recent() # miss 1, sets with default key
        cached_s1 = memcache.get('most_recent all') # hit 1
        self.assertEqual(s1.title, cached_s1.title, 'A korhazban')
        self.assertEqual(s1.difficulty, cached_s1.difficulty, 'Beginner')
        
        s2 = Story_most_recent(memcache_key="most_recent Intermediate", difficulty="Intermediate") # miss 2
        cached_s2 = memcache.get('most_recent Intermediate') # hit 2
        self.assertEqual(s2.title, cached_s2.title, 'Harry Potter')
        self.assertEqual(s2.difficulty, cached_s2.difficulty, 'Intermediate')
        
        Story(title="Blue", difficulty="Intermediate").put()
        
        # Without updating it should still return Harry Potter
        s3 = Story_most_recent(difficulty="Intermediate", memcache_key="most_recent Intermediate") # hit 3
        self.assertEqual(s3.title, "Harry Potter")
        
        s4 = Story_most_recent(difficulty="Intermediate", memcache_key="most_recent Intermediate", update=True) # hit 4
        cached_s4 = Story_most_recent(difficulty="Intermediate", memcache_key="most_recent Intermediate") # hit 5
        self.assertEqual(s4.title, "Blue")
        self.assertEqual(cached_s4.title, "Blue")
        
        stats = memcache.get_stats()
        self.assertEqual(stats['hits'], 5)
        self.assertEqual(stats['misses'], 2)
    
    def testStoryMostRecent(self):
        def Story_most_recent(difficulty="all", update=False):
            """
            returns the 50 most recent Storys of a given difficulty from memcache.
            If update=True then it returns from the datastore and writes to memcache.

            memcache_keys stored: 
            'most_recent all'
            'most_recent Beginner'
            'most_recent Intermediate'
            'most_recent Advanced'
            """
            key = "most_recent %s"%difficulty
            return _Story_most_recent(memcache_key=key, update=update, difficulty=difficulty)
        
        @memcached(memcache_key="most_recent all")
        def _Story_most_recent(difficulty="all"):
            q = Story.most_recent(difficulty)
            return [s for s in q.run(limit=50)]
        
        
        Story(title="Harry Potter", difficulty="Intermediate").put()
        Story_most_recent(difficulty="all", update=True) # miss 1
        Story_most_recent(difficulty="Intermediate", update=True) # miss 2
        
        Story(title="A korhazban", difficulty="Beginner").put()
        Story(title="An easy story", difficulty="Beginner").put()
        Story_most_recent(update=True) # hit 1 and write to db
        Story_most_recent(difficulty="Beginner", update=True) # miss 3
        
        
        s = Story_most_recent(difficulty="Beginner") # hit 2
        cached_s = memcache.get('most_recent Beginner') # hit 3
        
        self.assertEqual(2, len(s))
        self.assertEqual([(a.title, a.difficulty) for a in s],
                        [(a.title, a.difficulty) for a in cached_s])
        
        stats = memcache.get_stats()
        self.assertEqual(stats['hits'],3)
        self.assertEqual(stats['misses'], 3)
        
    




    



if __name__ == "__main__":
    unittest.main()
