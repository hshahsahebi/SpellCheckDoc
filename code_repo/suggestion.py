import re
import operator
from jellyfish import levenshtein_distance
from dictionary import Dictionary

class Suggestion:
    words_repo = dict()
    bigram_repo = dict()

    CODE_NON_WORD_ERR = 2
    CODE_REAL_WORD_ERR = 3
    CODE_RWE_IGNORED = 4
    CODE_CASE_ERR = 5

    def __init__(self):
        self.dictionary = Dictionary()
        self.active_word_repo = dict()

    def get_suggestions(self, word, prev_word, error_status, max_output = 5, max_len_diff = 2):
        start_len = 1 if (len(word[0]) - max_len_diff < 2) else len(word[0]) - max_len_diff
        end_len = len(word[0]) + max_len_diff + 1
        
        self.prepare_word_repo(start_len, end_len)
        self.select_lowest_distance(word[0].lower(), start_len, end_len)
        self.filter_active_repo(word, prev_word, error_status)
        output = self.select_best_suggestions()
        self.active_word_repo = dict()

        return output

    def prepare_word_repo(self, start_len, end_len):
        need_to_fetch = []

        for i in range(start_len, end_len):
            if(i not in self.words_repo):
                need_to_fetch.append(i)

        if(len(need_to_fetch) > 0):
            new_repo = self.dictionary.get_words_by_length(need_to_fetch)

            for words_set in new_repo:
                if(len(words_set) > 0):
                    for first_elem in words_set:
                        break
                    
                    self.words_repo[len(first_elem)] = words_set

    def select_lowest_distance(self, main_word, start_len, end_len):
        for length in range(start_len, end_len):
            if length in self.words_repo:
                for word in self.words_repo[length]:
                    if(type(word) is str and re.match(r"[a-zA-Z]", word) and main_word.lower() != word.lower()):
                        distance = levenshtein_distance(main_word, word)
                        if(distance < 3):
                            self.active_word_repo[word] = distance

    def filter_active_repo(self, current_word, prev_word, error_status):
        new_repo = dict()

        if(prev_word[0] == None):
            self.active_word_repo = new_repo
            return

        current_pos = current_word[1].lower()
        prev_pos = prev_word[1].lower()
        prev_word = prev_word[0].lower()

        for word in self.active_word_repo.keys():
            if word not in self.bigram_repo:
                self.bigram_repo[word] = self.dictionary.get_single_word_from_bigram(word)

            if self.bigram_repo[word] != None and prev_word in self.bigram_repo[word]['prev_words']:
                new_repo[word] = [self.active_word_repo[word], self.bigram_repo[word]['frequency']]
            elif(self.bigram_repo[word] != None and error_status != self.CODE_RWE_IGNORED and 
                current_pos in self.bigram_repo[word]['pos'] and 
                prev_pos in self.bigram_repo[word]['prev_pos']):
                new_repo[word] = [self.active_word_repo[word], 0]
            else:
                pass
                #Ignore the word if it doen't exist in previous words and positions
                #new_repo[word] = [self.active_word_repo[word], 0]

        self.active_word_repo = new_repo

    def select_best_suggestions(self):
        try:
            suggestions = sorted(self.active_word_repo.items(), key=lambda kv:(kv[1][0], 0-int(kv[1][1])))
        except TypeError:
            print('Sort Error: {}'.format(self.active_word_repo))

        result = list()
        
        for rec in suggestions:
            index = None
            sub_result = dict()

            for elem in rec:
                if(type(elem) is str):
                    sub_result[elem] = -1
                    index = elem
                elif(index != None):
                    sub_result[index] = elem[0]

            result.append(sub_result)

            if(len(result) == 5):
                break

        return result
        