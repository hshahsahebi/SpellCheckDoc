from flask import Flask, render_template, request, url_for, jsonify
import sys
sys.path.insert(0, '../code_repo')
from dictionary import Dictionary
from lookup import Lookup
from preprocessing import Preprocessing
import re
import time

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('index.html.j2')

@app.route('/dictionary')
def dictionary():
    my_dic = Dictionary()
    out_words = dict()
    out_words['dictionary'] = []
    out_words['common_words'] = []
    
    db_words = my_dic.get_words_by_length([i for i in range(1, 101)])
    db_common = my_dic.get_single_word_from_dic('common_words', type_set=True)

    for words_set in db_words:
        for elem in words_set:
            if(re.match(r"[a-zA-Z]", elem)):
                out_words['dictionary'].append({'word': elem})

    for common in db_common:
        out_words['common_words'].append({'word': common})

    return jsonify(out_words)

@app.route('/spellcheck', methods=['POST'])
def spellcheck():
    handler = Lookup()
    
    corrections = []
    words_processed = 0
    text = request.form['text']
    start_time = 0
    end_time = 0
     
    if(type(text) is str and len(text.strip()) > 0):
        start_time = time.time()
        fw = open('log.txt', 'a+', encoding='utf-8')
        fw.write("Proccessing Strated: {}\n".format(start_time))

        lines = handler.load_raw_text(passage=text.strip())
        fw.write("Lines fetched: {}\n".format(lines))

        for line_of_words in lines:
            prev_word = (None, None)
            prev_status = None
            words_processed += len(line_of_words)

            for word in line_of_words:
                word_result = handler.validate_word(word, prev_word)
                
                fw.write("Validation Result: {}\n".format(word_result))

                if(word_result['status'] != handler.CODE_CORRECT):
                    #If previous word is non-word ignore real-word error
                    if(prev_status == handler.CODE_NON_WORD_ERR and 
                        word_result['status'] in [handler.CODE_REAL_WORD_ERR, handler.CODE_RWE_IGNORED]):
                        fw.write("Included Status: Ignored (previous non-word)\n")
                        pass
                    #If previous word has real-word issue and also the current word has the same issue
                    #ignore it to prevent chain errors
                    elif(prev_status in [handler.CODE_REAL_WORD_ERR, handler.CODE_RWE_IGNORED] and 
                        word_result['status'] in [handler.CODE_REAL_WORD_ERR, handler.CODE_RWE_IGNORED]):
                        fw.write("Included Status: Ignored (previous real-word/rwe)\n")
                        pass
                    else:
                        fw.write("Included Status: Included\n")
                        corrections.append(word_result)
                    
                prev_word = word
                prev_status = word_result['status']


        end_time = time.time()
        fw.write("Proccessing Ended at {} in {} seconds\n".format(end_time, (end_time - start_time)))
        fw.write("----------------------------------------\n\n")
        fw.close()

    output = {
        'processed_words': words_processed,
        'duration': int(end_time) - int(start_time),
        'corrections': corrections
    }

    return jsonify(output)

@app.route('/add_to_dic', methods=['POST'])
def add_to_dic():
    word = request.form['word']
    word_pos = request.form['word_pos']
    prev_word = request.form['prev_word']
    prev_word_pos = request.form['prev_word_pos']
    next_word = request.form['next_word']
    next_word_pos = request.form['next_word_pos']

    dic = Dictionary()
    pp = Preprocessing()

    root_word = pp.fetch_lemmatized_word(word, word_pos)
    dic.add_single_word2dic(word, root_word)
    dic.add_single_word2bigram((word, word_pos), (prev_word, prev_word_pos))
    dic.add_single_word2bigram((next_word, next_word_pos), (word, word_pos))

    return "success"