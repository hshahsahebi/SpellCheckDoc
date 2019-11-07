from nltk import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import string
from collections import Counter
import re
from preprocessing import Preprocessing
from dictionary import Dictionary
from os import path

class Cleaner:

    def __init__(self):
        self.preprocessing = Preprocessing()

    def show_corpus_info(self, file_path = None, passage = None, store = True):

        if(file_path != None and path.exists(file_path)):
            corpus = open(file_path, 'r', encoding='utf-8').read()
        elif(passage != None):
            corpus = passage
        else:
            return False

        corpus = self.preprocessing.replace_urls(corpus, replace_with='')

        all_words = [word.lower() for word in word_tokenize(corpus) if len(word) > 0]
        unique_words = set(all_words)

        stop_words = stopwords.words("english") + list(string.punctuation + '®')

        all_processed_words = [word for word in all_words if word not in stop_words]
        unique_processed_words = [word for word in unique_words if word not in stop_words]

        words_counter = Counter(all_processed_words)
        most_common = words_counter.most_common(20)
        
        print("Number of words in corpus: {}".format(len(all_words)))
        print("Number of unique words is: {}".format(len(unique_words)))
        print("Number of non stop words in corpus: {}".format(len(all_processed_words)))
        print("Number of unique non stop words is: {}".format(len(unique_processed_words)))
        print("The most 30 common words are:\n{}".format(most_common))

        if(store):
            dic_handle = Dictionary()
            dic_handle.store_common_words(most_common)

    def clean_corpus(self, in_file = None, out_file = None, passage = None):

        if(in_file != None and path.exists(in_file)):
            corpus = open(in_file, 'r', encoding='utf-8').read().split("\n")
        elif(passage != None):
            corpus = passage.split("\n")
        else:
            return False
            
        corpus = self.remove_meaningless_lines(corpus)
        
        corpus = self.attach_incomplete_lines(' '.join(corpus))
        output = "\n".join(corpus).strip()

        if(out_file != None):
            fw = open(out_file, 'w+', encoding='utf-8')
            fw.write(output)
            fw.close()
            return True
        else:
            return output

    def bigram_preparation(self, in_file = None, out_file = None, passage = None):

        if(in_file != None and path.exists(in_file)):
            corpus = open(in_file, 'r', encoding='utf-8').read()
        elif(passage != None):
            corpus = passage
        else:
            return False
        
        new_corpus = self.preprocessing.impute_bigram_symbols(corpus).strip()

        if(out_file != None):
            fw = open(out_file, 'w+', encoding='utf-8')
            fw.write(new_corpus.strip())
            fw.close()
            return True
        else:
            return new_corpus

    '''
    @input: Array of lines in the corpus
    @output: Array of filtere lines in the corpus
    @description: The function removes empty lines and lines with lower length of 5
    after removing meaningless/inappropriate format words
    '''
    def remove_meaningless_lines(self, corpus):
        new_corpus = []

        for line in corpus:
            # Split the line into words
            words = self.preprocessing.customized_word_tokenizer(line)

            # Check each word to match a real word, number, date, time and remove it if not
            for wk, word in enumerate(words):
                if(not self.preprocessing.is_eligible_word(word)):
                    del words[wk]
                elif(wk == 0 and word == 'l'):
                    del words[wk]
                elif(re.match(r"www.it-ebooks.info", word)):
                    del words[wk]
                    

            # Replace the new filtered line 
            # Exclude lines if percentage of real words in the sentence is less than 40%
            # Exclude lines where the average length of words is less than 2
            if(len(words) > 0):
                real_words_length = 0
                all_length = 0

                for w in words:
                    all_length += len(w)
                    if(re.match(r"\b[A-Za-z’'-]+\b", w)):
                        real_words_length += len(w)

                if(all_length > 0 and (real_words_length / all_length) > 0.4 and 
                    (real_words_length / len(words)) >= 2):
                    new_corpus.append(' '.join(words).strip())

        return new_corpus


    '''
    @input: Textual corpus after removing invalid characters and phrases
    @output: Array of sentences
    @description: Using sentence tokenizer to append multiline sentences together and split each sentence
    '''
    def attach_incomplete_lines(self, corpus):
        corpus = re.sub(r"(\-\s)(?!$)", '', corpus)
        
        sentences = [re.sub(r"(\n+)|(\s+)", ' ', sentence.strip()) for sentence in sent_tokenize(corpus) 
            if len(re.sub(r"(\n+)|(\s+)", ' ', sentence.strip())) > 5]
        
        return sentences