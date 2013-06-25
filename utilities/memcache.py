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
                    for i in xrange(5):
                        client.gets(key)
                        if client.cas(key, result):
                            return result
                            
        return update_wrapper(memoized_f, f)


def test1():
    @memcached(key="hello")
    def hello_world(name, msg="hello"):
        return "%s says %s"%(name, msg)
    
    hello_world('joey')
    print 'tests pass'



if __name__ == '__main__':
    test1()


# old code

# def decorator(d):
#   """Make function d a decorator. It updates the __name__ and __doc__
#   of d to the new wrapped function."""
#   
#   def _d(fn):
#       return update_wrapper(d(fn),fn)
#   return update_wrapper(_d,d)
#   
# 
# @decorator
# def memcached(f):
#     def _f(*args, **kw):
#         """key and update will be overwritten on """
#         client = memcache.Client()
#         val = client.gets(key)
#         if val and not update:
#             return val
#         else:
#             val = f(key, update= *args, **kw)
#             for i in xrange(3):
#                 pass
#     return _f



