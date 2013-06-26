from base import HandlerBase
from models.kinds_and_queries import *


class QandABase(HandlerBase):
    def post(self):
        self.story = Story.by_id(int(self.request.get('story_id')))
        self.s_extras = StoryExtras.by_story(self.story.key())
        
        self.action()
        
    def action(self):
        pass
    
    def update_unanswered(self, new_q=False):
        were_unanswered = self.s_extras.has_unanswered_Q
        unanswered_Qs = Question.unanswered(self.story.key())
        if new_q:
            self.s_extras.has_unanswered_Q = True
            self.s_extras.put()
        elif were_unanswered and not unanswered_Qs:
            self.s_extras.has_unanswered_Q = False
            self.s_extras.put()
        elif not were_unanswered and unanswered_Qs:
            self.s_extras.has_unanswered_Q = True
            self.s_extras.put()
    

class AskQuestion(QandABase):
    def action(self):
        question = self.request.get('question').strip()
        
        q = Question(parent=self.story, question=question, uploader=self.student)
        q.put()
        q_key_e = encrypt(str(q.key()))
        
        self.update_unanswered(new_q=True)
        
        self.render('readstoryQandA.html', question=q, q_key_e=q_key_e)
    

class DeleteQuestion(QandABase):
    def action(self):
        q_key_e = self.request.get('q_key_e')
        q_key = db.Key(decrypt(q_key_e))
        a_keys = Answer.get_all_keys(q_key)
        db.delete(a_keys)
        db.delete(q_key)
        
        self.update_unanswered()
    

class AnswerQuestion(QandABase):
    def action(self):
        q_key_e = self.request.get('q_key_e')
        q_key = db.Key(decrypt(q_key_e))
        answer = self.request.get('answer').strip()
        
        a = Answer(parent=q_key, answer=answer, uploader=self.student)
        a.put()
        
        self.update_unanswered()
        
        self.render('readstoryQandA.html', answers=[(a, encrypt(str(a.key())))])
    

class DeleteAnswer(QandABase):
    def action(self):
        a_key = db.Key(decrypt(self.request.get('a_key_e')))
        
        db.delete(a_key)
        
        self.update_unanswered()
    

class IncrementThanks(QandABase):
    def post(self):
        a_key_e = self.request.get('a_key_e')
        a_key = db.Key(decrypt(a_key_e))
        a = db.get(a_key)
        a.thanks += 1
        a.put()
    



