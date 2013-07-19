from base import HandlerBase
from models.kinds_and_queries import *

class VocabBase(HandlerBase):
    def post(self):
        if not self.student:
            self.redirect('/signup')
        else:        
            self.story = Story_by_id(int(self.request.get('story_id')))
            self.vocabList = VocabList.retrieve(self.student.key(), self.story.key())
            if not self.vocabList:
                self.vocabList = VocabList(student=self.student, story=self.story)
        
            self.action()
    
    def action(self):
        pass
    


class UpdateVocab(VocabBase):
    def action(self):
        """Save my vocab."""
        hungarians = self.request.POST.getall("hung[]")
        meanings = self.request.POST.getall("mean[]")
        
        vocab_keys = []
        
        for (hungarian, meaning) in zip(hungarians, meanings):
            v = Vocab.retrieve(hungarian, meaning)
            if not v:
                v = Vocab(hungarian=hungarian, meaning=meaning)
                v.put()
            vocab_keys.append(v.key())
        
        self.vocabList.vocab_list = vocab_keys
        self.vocabList.put()
        # update VocabList queries
    



# OLD CODE        
# 
# class AddVocab(HandlerBase):
#     def post(self):
#         new_word = self.request.get("new_word").strip()
#         new_def = self.request.get("new_def").strip()
#         mode = self.request.get("mode")
#         
#         # retrieve the word from db or create it
#         v = Vocab.retrieve(new_word, new_def)
#         if not v:
#             v = Vocab(hungarian=new_word, meaning=new_def)
#             v.put()
#         v_key = v.key()
#         
#         # add the word to the vocab list
#         # these 4 lines can be abstracted out
#         story = Story_by_id(int(self.request.get('story_id')))
#         vl = VocabList.retrieve(self.student.key(), story.key())
#         if not vl:
#             vl = VocabList(student=self.student, story=story)
#             
#         if mode == 'normal':
#             vl.vocab_list.append(v_key)
#         elif mode == 'edit':
#             vl_index = int(self.request.get('vl_index'))
#             vl.vocab_list[vl_index] = v_key
#         vl.put()
#         
#         # return the new row
#         new_row = u'<tr id="{}"><td>{}</td><td>{}</td></tr>'.format(encrypt(str(v_key)), new_word, new_def)
#         self.response.write(new_row)
#     
# 
# class DeleteVocab(HandlerBase):
#     def post(self):
#         story = Story_by_id(int(self.request.get('story_id')))
#         vl = VocabList.retrieve(self.student.key(), story.key())
#         
#         vl_indices = map(int,self.request.POST.getall('vl_indices[]'))
#         vl.vocab_list[:] = [v for (i,v) in enumerate(vl.vocab_list) if i not in vl_indices]
#         vl.put()
#     
# 
# class ImportVocab(HandlerBase):
#     def post(self):
#         story = Story_by_id(int(self.request.get('story_id')))
#         
#         vl = VocabList.retrieve(self.student.key(), story.key())
#         if not vl:
#             vl = VocabList(student=self.student, story=story)
#             
#         keys_to_add_e = self.request.POST.getall('keys[]')
#         keys_to_add = map(db.Key, map(decrypt, keys_to_add_e))
#         
#         vl.vocab_list.extend(keys_to_add)
#         vl.put()
#     
# 
# class ReorderVocab(HandlerBase):
#     def post(self):
#         story = Story_by_id(int(self.request.get('story_id')))
#         vl = VocabList.retrieve(self.student.key(), story.key())
#         
#         keys_e = self.request.POST.getall('keys[]')
#         keys = map(db.Key, map(decrypt, keys_e))
#         
#         vl.vocab_list = keys
#         vl.put()
#     
# 

