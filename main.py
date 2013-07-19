import webapp2

from handlers.stories import Stories, AddStory, ReadStory
from handlers.vocab import UpdateVocab
from handlers.QandA import AskQuestion, DeleteQuestion, AnswerQuestion, DeleteAnswer, IncrementThanks
from handlers.comments import SaveComments
from handlers.mydesk import MyDesk
from handlers.authentication import Login, LogOut, SignUp
from handlers.onetimeuse import OneTimeUse


##### URL-HANDLER MAPPING
app = webapp2.WSGIApplication([
                               ('/?', Stories),
                               ('/addstory/?', AddStory),
                               ('/answerquestion/?', AnswerQuestion),
                               ('/askquestion/?', AskQuestion),
                               ('/deleteanswer/?', DeleteAnswer),
                               ('/deletequestion/?', DeleteQuestion),
                               ('/incrementthanks/?', IncrementThanks),
                               ('/login/?', Login),
                               ('/logout/?', LogOut),
                               ('/mydesk/?', MyDesk),
                               ('/onetimeuse/?', OneTimeUse),
                               ('/(\d+)', ReadStory),
                               ('/savecomments/?', SaveComments),
                               ('/signup/?', SignUp),
                               ('/updatevocab/?', UpdateVocab)
                              ],
                              debug=True)
