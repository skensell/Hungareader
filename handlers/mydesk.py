from base import HandlerBase
from models.kinds_and_queries import *

class MyDeskBase(HandlerBase):
    def initialize(self, *a, **kw):
        HandlerBase.initialize(self, *a, **kw)
        self.v_lists = self.student and [vl for vl in VocabList.by_student(self.student.key()) if vl.vocab_list]
        self.stories = self.student and [(vl.story, encrypt(str(vl.story.key()))) for vl in self.v_lists]
    

class MyDesk(MyDeskBase):
    def get(self):
        if not self.student: 
            self.redirect('/login')
        else:
            self.render("mydesk.html", stories=self.stories)
    
    def post(self):
        num_words = self.request.get('num_words')
        if num_words != 'all':
            num_words = int(num_words)
        random_or_not = self.request.get('random_or_not')
        which_stories_e = self.request.get_all('which_stories')
        which_stories = map(db.Key, map(decrypt, which_stories_e))
        
        words = []
        for vl in self.v_lists:
            if vl.story.key() in which_stories:
                words += Vocab.words_and_keys(vl)
        
        if random_or_not == 'random':
            words = random.sample(words, min(num_words, len(words)))
        else:
            if num_words != 'all':
                words = words[:num_words]
        
        self.render("mydesk.html", stories=self.stories, my_vocab=words,
                    which_stories_e=which_stories_e, num_words=str(num_words),
                    random_or_not=random_or_not)        
    
