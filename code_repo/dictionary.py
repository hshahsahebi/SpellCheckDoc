import redis
import re
from preprocessing import Preprocessing

class Dictionary:

    def __init__(self):
        self.redis_handler = redis.Redis(db=1, decode_responses=True)
        self.preprocessing = Preprocessing()

        self.prepared_dic = dict()
        self.prepared_bigram = dict()
        self.prepared_lencat = dict()
        
        self.bigram_prefix = 'bigram_'
        self.lencat_prefix = 'lencat_'

        self.DB_DICTIONARY = 'dic_exists'
        self.DB_BIGRAM = 'bigram_exists'
        self.DB_LENCAT = 'lencat_exists'
        self.DB_COMMON = 'common_exists'

        self.CASE_UPPER = '1'
        self.CASE_LOWER = '2'
        self.CASE_BOTH = '0'

    def words_really_different(self, main_word, lemma_word):
        pattern = "^{}(es|s)?$".format(lemma_word.lower())
        try:
            if(not re.match(r"^[a-zA-Z]+$", main_word)):
                return False

            if(re.match(pattern, main_word.lower())):
                return False
        except re.error as e:
            print("{}: {}".format(pattern, main_word.lower()))
            raise Exception(str(e))

        return True

    def database_exists(self, keyword):
        return True if self.get_single_word_from_dic(keyword) == '1' else False

    def prepare_word2dic(self, main_word, root_word):
        word2store = root_word.lower()

        prev_case = self.prepared_dic[word2store] if word2store in self.prepared_dic else None
        current_case = self.get_word_case(main_word, prev_case=prev_case)
        self.prepared_dic[word2store] = current_case

        if(self.words_really_different(main_word, root_word)):
            self.prepared_dic[main_word.lower()] = current_case

        self.prepare_lencat2dic(main_word, root_word)

    def prepare_lencat2dic(self, main_word, root_word):
        word1 = root_word.lower()
        word2 = main_word.lower()

        lencat_index = "{}{}".format(self.lencat_prefix, len(word1))
        if(lencat_index in self.prepared_lencat):
            self.prepared_lencat[lencat_index].add(word1)
        else:
            self.prepared_lencat[lencat_index] = {word1}

        if(word1 != word2):
            lencat_index = "{}{}".format(self.lencat_prefix, len(word2))
            if(lencat_index in self.prepared_lencat):
                self.prepared_lencat[lencat_index].add(word2)
            else:
                self.prepared_lencat[lencat_index] = {word2}

    def prepare_bigram2dic(self, word, prev_word):
        word2look = "{}{}".format(self.bigram_prefix, word[0].lower())
        word_pos = word[0] if self.preprocessing.is_customized_word(word[0]) else word[1]
        prev_w = None if prev_word[0] == None else prev_word[0]
        
        if(prev_word[0] == None):
            prev_p = None
        elif(self.preprocessing.is_customized_word(prev_word[0])):
            prev_p = prev_word[0]
        else:
            prev_p = prev_word[1]

        if(word2look in self.prepared_bigram):
            self.prepared_bigram[word2look]['pos'].add(word_pos.lower())
            self.prepared_bigram[word2look]['frequency'] += 1

            if(prev_w != None):
                self.prepared_bigram[word2look]['prev_words'].add(prev_w.lower())

            if(prev_p != None):
                self.prepared_bigram[word2look]['prev_pos'].add(prev_p.lower())
        else:
            self.prepared_bigram[word2look] = {
                'pos': {word_pos.lower()},
                'frequency': 1,
                'prev_words': set() if prev_w == None else {prev_w.lower()},
                'prev_pos': set() if prev_p == None else {prev_p.lower()}
            }

    def store_prepared_data(self):
        result = False
        set_dbs = set()

        if(len(self.prepared_dic) > 0):
            if(self.redis_handler.mset(self.prepared_dic)):
                result = True
                set_dbs.add(self.DB_DICTIONARY)
        if(len(self.prepared_bigram) > 0):
            with self.redis_handler.pipeline() as pipe:
                for word, data in self.prepared_bigram.items():
                    try:                            
                        pipe.set("{}_frequency".format(word), data['frequency'])
                        if(len(data['pos']) > 0):
                            pipe.sadd("{}_pos".format(word), *data['pos'])
                        if(len(data['prev_words']) > 0):
                            pipe.sadd("{}_prev_words".format(word), *data['prev_words'])
                        if(len(data['prev_pos']) > 0):
                            pipe.sadd("{}_prev_pos".format(word), *data['prev_pos'])
                    except TypeError as e:
                        print(str(e))
                        print("{}: {}".format(word, data))
                        return

                pipe_result = pipe.execute()

            if(not False in pipe_result):
                result = True
                set_dbs.add(self.DB_BIGRAM)
        if(len(self.prepared_lencat) > 0):
            
            with self.redis_handler.pipeline() as pipe:
                for index, words in self.prepared_lencat.items():
                    pipe.sadd(index, *words)

                pipe_result = pipe.execute()

            if(not False in pipe_result):
                result = True
                set_dbs.add(self.DB_LENCAT)
            else:
                print("{} => {}".format(self.DB_BIGRAM, pipe_result))
        
        if(result):
            with self.redis_handler.pipeline() as pipe:
                for db in set_dbs:
                    self.redis_handler.set(db, '1')
                
                pipe.execute()

        self.prepared_dic = dict()
        self.prepared_bigram = dict()
        self.prepared_lencat = dict()
        
        return result

    def add_single_word2dic(self, main_word, root_word):
        word2store = root_word.lower()
        value = self.get_single_word_from_dic(root_word)
        word_type = self.get_word_case(main_word, prev_case=value)

        with self.redis_handler.pipeline() as pipe:
            pipe.set(word2store, word_type)
            pipe.sadd("{}{}".format(self.lencat_prefix, len(word2store)), word2store)
            if(self.words_really_different(main_word, root_word)):
                pipe.set(main_word.lower(), word_type)
                pipe.sadd("{}{}".format(self.lencat_prefix, len(main_word)), main_word.lower())

            pipe.execute()

        return word_type

    def get_single_word_from_dic(self, word2look, bigram = False, postfix = None, type_set = False):
        word = word2look.lower() if not bigram else "{}{}_{}".format(self.bigram_prefix, word2look.lower(), postfix)

        word = self.redis_handler.get(word) if not type_set else self.redis_handler.smembers(word)

        if(word != None and type(word) is not set):
            return word
        elif(word != None and type(word) is set and len(word) > 0):
            return set([term for term in word if term != None])

        return None

    def add_single_word2bigram(self, word, prev_word):
        word2look = "{}{}".format(self.bigram_prefix, word[0].lower())
        word_pos = word[0] if self.preprocessing.is_customized_word(word[0]) else word[1]
        prev_w = None if prev_word[0] == None else prev_word[0]
        
        if(prev_w == None):
            prev_p = None
        elif(self.preprocessing.is_customized_word(prev_w)):
            prev_p = prev_w
        else:
            prev_p = prev_word[1]

        with self.redis_handler.pipeline() as pipe:
            if(self.get_single_word_from_dic("{}_frequency".format(word2look)) != None):
                pipe.incr("{}_frequency".format(word2look))
            else:
                pipe.set("{}_frequency".format(word2look), 1)

            pipe.sadd("{}_pos".format(word2look), *{word_pos.lower()})

            if(prev_w != None):
                pipe.sadd("{}_prev_words".format(word2look), *{prev_w.lower()})

            if(prev_p != None):
                pipe.sadd("{}_prev_pos".format(word2look), *{prev_p.lower()})

            print(word)

            pipe.execute()

    def get_single_word_from_bigram(self, word):
        frequency = self.get_single_word_from_dic(word, bigram=True, postfix='frequency')

        if(frequency != None):
            return {
                'pos': self.get_single_word_from_dic(word, bigram=True, postfix='pos', type_set=True),
                'frequency': frequency,
                'prev_words': self.get_single_word_from_dic(word, bigram=True, postfix='prev_words', type_set=True),
                'prev_pos': self.get_single_word_from_dic(word, bigram=True, postfix='prev_pos', type_set=True)
            }

        return None

    def get_word_case(self, word, prev_case = None):
        if(prev_case == None):
            return self.CASE_UPPER if word.isupper() else self.CASE_LOWER
        elif(prev_case == self.CASE_BOTH):
            return self.CASE_BOTH
        else:
            current_case = self.get_word_case(word)
            return self.CASE_BOTH if current_case != prev_case else current_case

    def get_words_by_length(self, length_list):
        pipe_result = []

        with self.redis_handler.pipeline() as pipe:
            for index in length_list:
                pipe.smembers("{}{}".format(self.lencat_prefix, index))

            pipe_result = pipe.execute()

        return pipe_result  

    def store_common_words(self, words):
        if(not self.database_exists(self.DB_COMMON)):
            common_words = set()

            for word in words:
                for cw in word:
                    break
                common_words.add(cw)

            if(len(common_words) > 0 and self.redis_handler.sadd('common_words', *common_words)):
                self.redis_handler.set(self.DB_COMMON, '1')        