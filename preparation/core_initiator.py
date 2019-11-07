import os
import sys
sys.path.insert(0, "../code_repo")
from pdf_to_text import convert_pdf_to_txt as p2t
from corpus_cleaning import Cleaner
from dictionary_creator import create_dictionary, create_bigram

'''
Look in resource folder for corpus.txt
If it does not exist try to convert the pdf format of corpus to text format
'''
if(not os.path.exists('resources/corpus.txt')):
    p2t('resources/corpus.pdf')

cleaner = Cleaner()

if(not os.path.exists('resources/corpus_cleansed.txt')):
    cleaner.clean_corpus(in_file='resources/corpus.txt', out_file='resources/corpus_cleansed.txt')

cleaner.show_corpus_info(file_path='resources/corpus_cleansed.txt')

if(not os.path.exists('resources/corpus_symbolic.txt')):
    cleaner.bigram_preparation(in_file='resources/corpus_cleansed.txt', out_file='resources/corpus_symbolic.txt')


if(create_dictionary()):
    print("Dictionary created successfully!")
else:
    print("Dictionary is already created!")

if(create_bigram()):
    print("Bigram created successfully!")
else:
    print("Bigram is already created!")