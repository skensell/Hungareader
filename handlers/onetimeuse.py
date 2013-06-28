from base import HandlerBase
from models.kinds_and_queries import *

class OneTimeUse(HandlerBase):
    def get(self):
        # put code here
        #memcache.flush_all()
        
        self.write("Success!")
    
    def replace_stories(self):
        """Give each story the parent."""
        stories = [s for s in Story.all().run()]
        for i in xrange(len(stories)):
            s = stories[i]
            
            new_s = clone_entity(s, parent=StoryParent_key())
            # I should also have made a new_s_extras and initialized it.
            new_s.put()
            
            db.delete(db.query_descendants(s).run(limit=100))
            
            s.delete()
    
    def add_new_story_extras(self):
        """Give story_extras to each story"""
        stories = [s for s in Story.all().run()]
        for s in stories:
            se = StoryExtras(parent=s.key())
            se.put()
    


        
    

def clone_entity(e, **extra_args):
    """
    Taken from stackoverflow.
    Clones an entity, adding or overriding constructor attributes.
    The cloned entity will have exactly the same property values as the original
    entity, except where overridden. By default it will have no parent entity or
    key name, unless supplied.
    Args:
    e: The entity to clone
    extra_args: Keyword arguments to override from the cloned entity and pass
      to the constructor.
    Returns:
    A cloned, possibly modified, copy of entity e.
    """
    klass = e.__class__
    props = dict((k, v.__get__(e, klass)) for k, v in klass.properties().iteritems())
    props.update(extra_args)
    return klass(**props)
    


