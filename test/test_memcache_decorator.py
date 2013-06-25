# When writing your test code, please follow the Python unit test coding conventions (http://docs.python.org/lib/writing-tests.html). Here are some simple rules:
#   * All test modules should be named like 'test_xxx'. (This is not strictly necessary for GAEUnit.)
#   * All test classes must extend unittest.TestCase
#   * All test functions name must be in the format of 'testXxx'

import unittest
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed




class TestModel(db.Model):
  """A model class used for testing."""
  number = db.IntegerProperty(default=42)
  text = db.StringProperty()

class TestEntityGroupRoot(db.Model):
  """Entity group root"""
  pass

def GetEntityViaMemcache(entity_key):
  """Get entity from memcache if available, from datastore if not."""
  entity = memcache.get(entity_key)
  if entity is not None:
    return entity
  entity = TestModel.get(entity_key)
  if entity is not None:
    memcache.set(entity_key, entity)
  return entity  





class DemoTestCase(unittest.TestCase):
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
    def testInsertEntity(self):
        TestModel().put()
        self.assertEqual(1, len(TestModel.all().fetch(2)))
    
    def testFilterByNumber(self):
        root = TestEntityGroupRoot(key_name="root")
        TestModel(parent=root.key()).put()
        TestModel(number=17, parent=root.key()).put()
        query = TestModel.all().ancestor(root.key()).filter('number =', 42)
        results = query.fetch(2)
        self.assertEqual(1, len(results))
        self.assertEqual(42, results[0].number)
    
    def testGetEntityViaMemcache(self):
        entity_key = str(TestModel(number=18).put())
        retrieved_entity = GetEntityViaMemcache(entity_key)
        self.assertNotEqual(None, retrieved_entity)
        self.assertEqual(18, retrieved_entity.number)
    



if __name__ == "__main__":
    unittest.main()


