import os
import sys
import random
import json
sys.path.insert(0, "../code_repo")
from lookup import Lookup

source_file = 'resources/corpus_cleansed.txt'
destination_validation = 'resources/validation/'

options_tuple = ('NW', 'RW', 'BO')
validations_set = []
maximum_limit = 100
lookup = Lookup()

def is_init():
    for counter in range (1, 4):
        for opt in options_tuple:
            if(not os.path.exists("{}{}_{}.txt".format(destination_validation, opt, counter)) and 
                not os.path.exists("{}{}_{}.ready.txt".format(destination_validation, opt, counter))):
                return True
    return False


if(not os.path.exists(source_file)):
    print("Cleaned corpus does not exist")
    sys.exit()


if(is_init()):
    print("Initialization...")
    corpus = open(source_file, 'r', encoding='utf-8').read().split("\n")

    random_numbers = [i for i in range(0, len(corpus))]

    for counter in range(0, 3):
        for c2 in range(0, 3):
            valset = []
            word_numbers = 0

            while(word_numbers <= maximum_limit):
                corpus_index = random.choice(random_numbers)

                try:
                    if(word_numbers + len(corpus[corpus_index].split(" ")) > maximum_limit):
                        if(word_numbers > (maximum_limit/2)):
                            break
                        else:
                            continue
                except IndexError:
                    random_numbers.remove(corpus_index)
                    continue

                word_numbers += len(corpus[corpus_index].split(" "))
                valset.append(corpus[corpus_index])
                corpus.pop(corpus_index)
                random_numbers.remove(corpus_index)

            if(c2 == 0):
                validations_set.append(["\n".join(valset)])
            else:
                validations_set[counter].append("\n".join(valset))

    for counter in range (0, 3):
        for c2 in range(0, 3):
            print("Creating file for {}{}_{}.txt ...".format(destination_validation, options_tuple[counter], c2 + 1))
            fw = open("{}{}_{}.txt".format(destination_validation, options_tuple[counter], c2 + 1), 'w+', encoding='utf-8')
            fw.write(validations_set[counter][c2])
            fw.close()


for counter in range (1, 4):
    for opt in options_tuple:
        file_s = "{}{}_{}.ready.txt".format(destination_validation, opt, counter)
        file_d = "{}{}_{}.result.txt".format(destination_validation, opt, counter)

        if(not os.path.exists(file_d) and os.path.exists(file_s)):
            print("Spell Check in Progress for {} ...".format(file_s))
            lines = lookup.load_raw_text(file_path=file_s)
            corrections = []
            corrected_words = []

            for line_of_words in lines:
                prev_word = (None, None)

                for word in line_of_words:
                    word_result = lookup.validate_word(word, prev_word)
                    if(opt == 'NW' and word_result['status'] == lookup.CODE_NON_WORD_ERR):
                        corrections.append(word_result)
                        corrected_words.append(word_result['word'][0])
                        print("NW Correction added...")
                    elif(opt == 'RW' and word_result['status'] in [lookup.CODE_REAL_WORD_ERR, 
                        lookup.CODE_RWE_IGNORED]):
                        corrections.append(word_result)
                        corrected_words.append(word_result['word'][0])
                        print("RW Correction added...")
                    elif(opt == 'BO' and word_result['status'] not in [lookup.CODE_CASE_ERR, 
                        lookup.CODE_CORRECT]):
                        corrections.append(word_result)
                        corrected_words.append(word_result['word'][0])
                        print("RW/NW Correction added...")

                    prev_word = word
            
            fw = open(file_d, 'w+', encoding='utf-8')
            fw.write("This file includes {} records.\n".format(len(corrections)))
            fw.write("Corrected words are as follow:\n")
            fw.write(json.dumps(corrected_words, sort_keys=False, indent=4))
            fw.write(json.dumps(corrections, sort_keys=False, indent=4))
            fw.close()
            print("File {} created.".format(file_d))