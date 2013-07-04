import webapp2

from handlers.stories import Stories, AddStory, ReadStory
from handlers.vocab import AddVocab, DeleteVocab, ImportVocab, ReorderVocab
from handlers.QandA import AskQuestion, DeleteQuestion, AnswerQuestion, DeleteAnswer, IncrementThanks
from handlers.comments import SaveComments
from handlers.mydesk import MyDesk
from handlers.authentication import Login, LogOut, SignUp
from handlers.onetimeuse import OneTimeUse


##### URL-HANDLER MAPPING
app = webapp2.WSGIApplication([
                               ('/?', Stories),
                               ('/addstory/?', AddStory),
                               ('/addvocab/?', AddVocab),
                               ('/answerquestion/?', AnswerQuestion),
                               ('/askquestion/?', AskQuestion),
                               ('/deleteanswer/?', DeleteAnswer),
                               ('/deletequestion/?', DeleteQuestion),
                               ('/deletevocab/?', DeleteVocab),
                               ('/importvocab/?', ImportVocab),
                               ('/incrementthanks/?', IncrementThanks),
                               ('/login/?', Login),
                               ('/logout/?', LogOut),
                               ('/mydesk/?', MyDesk),
                               ('/onetimeuse/?', OneTimeUse),
                               ('/reordervocab/?', ReorderVocab),
                               ('/(\d+)', ReadStory),
                               ('/savecomments/?', SaveComments),
                               ('/signup/?', SignUp)
                              ],
                              debug=True)
