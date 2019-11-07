import re
from preprocessing import Preprocessing
from dictionary import Dictionary
from corpus_cleaning import Cleaner
from suggestion import Suggestion

class Lookup:

    CODE_PENDING = 0
    CODE_CORRECT = 1
    CODE_NON_WORD_ERR = 2
    CODE_REAL_WORD_ERR = 3
    CODE_RWE_IGNORED = 4
    CODE_CASE_ERR = 5

    def __init__(self):
        self.preprocessing = Preprocessing()
        self.dictionary = Dictionary()
        self.cleaner = Cleaner()
        self.suggestion = Suggestion()

        self.word_val_in_dic = None
        self.word_val_in_bigram = None
        self.word_status_code = self.CODE_PENDING

        self.textual_status = {
            0: 'In_Progress',
            1: 'Correct Word',
            2: 'Non-Word Error',
            3: 'Real-Word Error',
            4: 'Real-Word Error Ignored',
            5: 'Case Error'
        }

    def load_raw_text(self, file_path = None, passage = None):
        if(file_path == None and passage == None):
            raise Exception('File path or passage should be provided. File path has priority!')
        
        text = self.cleaner.clean_corpus(in_file=file_path, passage=passage)
        
        if(text):
            text = self.cleaner.bigram_preparation(passage=text)
            
            return [self.preprocessing.fetch_line_words(line, escape_symbols=False) for line in text.split("\n")]

        return []
  
    def validate_word(self, word, prev_word):
        if(self.preprocessing.is_customized_word(word[0])):
            lemma = word[0]
        else:
            lemma = self.preprocessing.fetch_lemmatized_word(word[0], word[1])

        suggestions = dict()

        if(self.word_exists(word[0], lemma)):
            if(self.word_in_real_place(word, prev_word)):
                if(self.word_in_correct_case(word[0])):
                    self.word_status_code = self.CODE_CORRECT
                else:
                    self.word_status_code = self.CODE_CASE_ERR
            elif(self.word_can_be_real(word, prev_word)):
                self.word_status_code = self.CODE_RWE_IGNORED
            else:
                self.word_status_code = self.CODE_REAL_WORD_ERR
        else:
            self.word_status_code = self.CODE_NON_WORD_ERR

        if(self.word_status_code not in [self.CODE_CORRECT, self.CODE_CASE_ERR]):
            suggestions = self.suggestion.get_suggestions(word, prev_word, self.word_status_code)
            if(word[0].lower() in suggestions):
                self.word_status_code = self.CODE_CORRECT

        return {
            'word': word,
            'prev_word': prev_word,
            'status': self.word_status_code,
            'textual_status': self.textual_status[self.word_status_code],
            'lemma': lemma,
            'suggestions': suggestions
        }

    def word_exists(self, main_word, lemmatized_word):
        if(self.preprocessing.is_customized_word(main_word)):
            self.word_val_in_dic = self.dictionary.CASE_BOTH
            return True

        self.word_val_in_dic = self.dictionary.get_single_word_from_dic(lemmatized_word)

        if(self.word_val_in_dic == None and self.dictionary.words_really_different(main_word, lemmatized_word)):
            self.word_val_in_dic = self.dictionary.add_single_word2dic(main_word, lemmatized_word)

        return False if self.word_val_in_dic == None else True

    def word_in_real_place(self, word, prev_word):
        if(prev_word[0] == None):
            return True
        else:
            self.word_val_in_bigram = self.dictionary.get_single_word_from_bigram(word[0])

            if(self.word_val_in_bigram != None and 
                prev_word[0].lower() in self.word_val_in_bigram['prev_words']):
                return True

        return False

    def word_can_be_real(self, word, prev_word):
        prev_pos = prev_word[0] if self.preprocessing.is_customized_word(prev_word[0]) else prev_word[1]
        
        if(self.word_val_in_bigram != None and prev_pos != None and 
            self.word_val_in_bigram['pos'] != None and 
            self.word_val_in_bigram['prev_pos'] != None and
            word[1].lower() in self.word_val_in_bigram['pos'] and 
            prev_pos.lower() in self.word_val_in_bigram['prev_pos']):
            
            return True

        return False

    def word_in_correct_case(self, main_word):
        if(re.match(r"^([A-Z][a-z]+(\-\_)?)+$", main_word)):
            main_word = main_word.lower()

        if(re.match(r"^[A-Z]+(s|es)$", main_word)):
            main_word = re.sub(r"(s|es)$", '', main_word)
            new_val = self.dictionary.get_single_word_from_dic(main_word)
            if(new_val != None):
                self.word_val_in_dic = new_val

        if(len(main_word) > 1 and not main_word[1:].islower() and not main_word[1:].isupper()):
            return False

        if(self.word_val_in_dic == None):
            return True

        current_case = self.dictionary.get_word_case(main_word)

        if(self.word_val_in_dic == self.dictionary.CASE_BOTH or current_case == self.word_val_in_dic):
            return True

        return False