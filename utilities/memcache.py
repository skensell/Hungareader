from functools import update_wrapper
from google.appengine.api import memcache


class memcached(object):
    def __init__(self, key="some_key", *args, **kw):
        self.key = key
    
    def __call__(self, f):
        """This is called just once when we use @memcached()"""
        def memoized_f(key=self.key, update=False, *args, **kw):
            client = memcache.Client()
            val = client.gets(key)
            if val != None and not update:
                return val
            else:   
                result = f(*args,**kw) # hits the datastore
                
                if val is None: # add it for the first itme
                    client.add(key, result)
                    return result
                    
                else:
                    # avoid race conditions which may happen if multiple people
                    # try to update at the same time
                    for i in xrange(3):
                        if client.cas(key, result):
                            return result
                        client.gets(key)
                            
        return update_wrapper(memoized_f, f)




