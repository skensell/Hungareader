from base import HandlerBase
from models.kinds_and_queries import *

from utilities.youtube_api import get_video_id



class Stories(HandlerBase):
    def get(self):
        type_filter = self.request.get('type_filter') or 'most_recent'
        difficulty = self.request.get('difficulty') or 'all'
        
        if type_filter == 'most_recent':
            stories = Story_most_recent(difficulty=difficulty)
        elif type_filter == 'unanswered':
            stories = Story_unanswered(difficulty=difficulty)
        
        self.render('stories.html', stories=stories, type_filter=type_filter,
                    difficulty=difficulty)    
    

class AddStory(HandlerBase):
    def get(self):
        if not self.student:
            self.redirect("/login")
        else:
            self.render("addstory.html")
    
    def post(self):
        title = self.request.get('title').strip()
        author = self.request.get('author').strip()
        summary = self.request.get('summary').strip()
        text = self.request.get('story').rstrip()
        video_url = self.request.get('video_url').strip()
        tags = map(lambda x: x.strip(), self.request.get('tags').split(','))
        difficulty = self.request.get('difficulty')
        
        error_msg = "Please fill out all required fields."
        
        if not (title and author and summary and text and difficulty):
            self.render("addstory.html", error=error_msg, title=title, author=author, summary=summary,
                        story=text, difficulty=difficulty, video_url=video_url )
        else:
            # add the story and update cache
            uploader = self.student
            video_id = get_video_id(video_url)
            if len(tags) == 1 and tags[0] == '':
                tags = []
            
            s = Story(parent=StoryParent_key(), title=title, author=author, summary=summary, text=text,
                    difficulty=difficulty, uploader=uploader, video_id=video_id, tags=tags)
            story_key = s.put()
            
            story_extras = StoryExtras(parent=story_key)
            story_extras.put()
            
            self.update_cache(difficulty)
            
            self.redirect("/%s"%story_key.id())
    
    def update_cache(self, difficulty):
        Story_most_recent(difficulty="all", update=True)
        Story_most_recent(difficulty=difficulty, update=True)
    

class ReadStory(HandlerBase):
    def get(self, story_id):
        story = Story_by_id(int(story_id))
        story_key = story.key()
        # logging.info([story.text])
        
        my_vocab = []
        if self.student:
            vl = VocabList_retrieve(student_key=self.student.key(), story_key=story_key)
            my_vocab = Vocab.words_and_keys(vl)
        
        v_lists = []
        for vl in VocabList_by_story(story_key):
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
    


