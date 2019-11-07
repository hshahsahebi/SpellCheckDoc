from preprocessing import Preprocessing
from dictionary import Dictionary
import re
import os

def create_dictionary(in_file = None, passage = None):
    if(in_file != None and os.path.exists(in_file)):
        corpus_lines = open(in_file, 'r', encoding='utf-8').read().split("\n")
    elif(passage != None):
        corpus_lines = passage.split("\n")
    else:
        print("Invalid input!")
        return

    d = Dictionary()
    p = Preprocessing()
    
    if(d.database_exists(d.DB_DICTIONARY)):
        return False
    

    for line in corpus_lines:
        words = p.fetch_line_words(line)
        
        for word in words:
            main_word = re.sub(r"[^-A-Za-z0-9]", '', word[0])
            root = p.fetch_lemmatized_word(main_word, word[1])
            d.prepare_word2dic(main_word, root)

    return d.store_prepared_data()

def create_bigram(in_file = None, passage = None):
    if(in_file != None and os.path.exists(in_file)):
        corpus_lines = open(in_file, 'r', encoding='utf-8').read().split("\n")
    elif(passage != None):
        corpus_lines = passage.split("\n")
    else:
        print("Invalid input!")
        return

    d = Dictionary()
    p = Preprocessing()

    if(d.database_exists(d.DB_BIGRAM)):
        return False
    

    for line in corpus_lines:
        words = p.fetch_line_words(line, escape_symbols=False)
        prev_word = (None, None)

        for word in words:
            d.prepare_bigram2dic(word, prev_word)
            prev_word = word

    return d.store_prepared_data()