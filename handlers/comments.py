from base import HandlerBase
from models.kinds_and_queries import *

class SaveComments(HandlerBase):
    def post(self):
        story = Story.by_id(int(self.request.get('story_id')))
        s_extras = StoryExtras.by_story(story.key())
        comments = self.request.get('comments_text').strip()
        
        s_extras.comments = comments
        s_extras.put()
    
