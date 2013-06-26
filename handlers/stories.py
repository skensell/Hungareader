from base import HandlerBase
from models.kinds_and_queries import *

from utilities.youtube_api import get_video_id



class Stories(HandlerBase):
    def get(self):
        type_filter = self.request.get('type_filter') or 'most_recent'
        difficulty = self.request.get('difficulty') or 'all'
        
        stories_w_extras = recent_stories_w_extras(type_filter, difficulty);
        
        self.render('stories.html', stories_w_extras=stories_w_extras, type_filter=type_filter,
                    difficulty=difficulty)    
    

class AddStory(HandlerBase):
    def get(self):
        if not self.student:
            self.redirect("/login")
        else:
            self.render("addstory.html")
    
    def post(self):
        title = self.request.get('title').strip()
        summary = self.request.get('summary').strip()
        text = self.request.get('story').rstrip()
        video_url = self.request.get('video_url').strip()
        difficulty = self.request.get('difficulty')
        
        error_msg = "Please fill out all required fields."
        
        if not (title and summary and text):
            self.render("addstory.html", error=error_msg, title=title, summary=summary,
                        story=text, difficulty=difficulty, video_url=video_url )
        else:
            uploader = self.student
            video_id = get_video_id(video_url)
            s = Story(title=title, summary=summary, text=text,
                difficulty=difficulty, uploader=uploader, video_id=video_id)
            story_key = s.put()
            
            story_extras = StoryExtras(parent=story_key)
            story_extras.put()
            
            self.redirect("/%s"%story_key.id())
    

class ReadStory(HandlerBase):
    def get(self, story_id):
        story = Story.by_id(int(story_id))
        story_key = story.key()
        # logging.info([story.text])
        
        my_vocab = []
        if self.student:
            vl = VocabList.retrieve(self.student.key(), story_key)
            my_vocab = Vocab.words_and_keys(vl)
        
        v_lists = []
        for vl in VocabList.by_story(story_key):
            vocabs = Vocab.words_and_keys(vl)
            num_words = len(vocabs)
            v_lists.append((vl, num_words, vocabs))
        
        QandA = []
        for q in Question.by_story(story_key):
            q_key = q.key()
            q_key_e = encrypt(str(q_key))
            answers = [(a, encrypt(str(a.key()))) for a in Answer.by_question(q_key)]
            QandA.append((q, q_key_e, answers))
        
        story_extras = StoryExtras.by_story(story_key)
        
        self.render("readstory.html", story=story, my_vocab=my_vocab, v_lists=v_lists,
                    QandA=QandA, story_extras=story_extras)
    


