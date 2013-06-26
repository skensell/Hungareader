from functools import update_wrapper
from google.appengine.api import memcache

class memcached(object):
    """
    This is a decorator for storing query results in memcache.
    
    @memcached(memcache_key='some_query')
    def q(**kw):
        return [s for s in Story.all().run()]
    
    r = q(memcache_key='my_favorite_key', **kw)
    
    Each time a new key is given to q it hits the datastore, stores it in memcache, and returns it.
    Each time an old key is given it hits the memcache and returns it, unless update=True, in which
    case it hits the datastore, stores it in memcache, and returns it.
    If q is called with no "key" argument, the default key of "some_query" will be used.
    
    See test_memcache_decorator.py for detailed unittests.
    
    """
    def __init__(self, memcache_key="DEFAULT_KEY", *args, **kw):
        self.key = memcache_key
    
    def __call__(self, f):
        """This is called just once when we use @memcached()"""
        def memoized_f(memcache_key=self.key, update=False, *args, **kw):
            key = memcache_key
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


