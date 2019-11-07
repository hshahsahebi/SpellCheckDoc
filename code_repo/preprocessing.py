import re
from nltk import word_tokenize, sent_tokenize, pos_tag
import string
import redis
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet


class Preprocessing:

    def __init__(self):
        self.customized_symbols = {
            'date': '|DATE|',
            'time': '|TIME|',
            'url': '|URL|',
            'number': '|NUMBER|',
            'sent_start': '|STARTSENT|',
            'sent_end': '|ENDSENT|'
        }

        self.lemmatizer = WordNetLemmatizer()

    '''
    @input: String representing a sentence or group of words
    @output: Array representing all words in the input string
    '''
    def customized_word_tokenizer(self, phrase):
        singular_tokens = ['.', '?', '!', ',', ';', '-', '_']
        removal_tokens = ['(', ')', '"', "'", '[', ']']

        phrase = re.sub(r"\s+", ' ', phrase.strip())

        for t in singular_tokens:
            patt = '([\\' + t + ']\\s)+'
            phrase = re.sub(patt, t + ' ', phrase)
            patt = '(\\s[\\' + t + '])+'
            phrase = re.sub(patt, ' ' + t, phrase)
            patt = '[\\' + t + ']+'
            phrase = re.sub(patt, t, phrase)

        for t in removal_tokens:
            patt = '[\\' + t + ']+'
            phrase = re.sub(patt, t, phrase)
            
        phrase = re.sub(r"\s+", ' ', phrase.strip())
            
        return phrase.split(' ')

    '''
    @input: String representing a word
    @output: Boolean representing whether the string can be considered as a word or not
    @description: The string shoud be numeric or alphabetic to be considered as word. 
    Some symbols that can be mixed with the numbers and alphabets are also considered.
    '''
    def is_eligible_word(self, word):
        word = re.sub(r"^[\#\(\"\'\“]", '', word)
        word = re.sub(r"[\)\"\'\”\;\.\?\!\,]+$", '', word)

        if((re.match(r"^[A-Za-z]+[\-\_]?[A-Za-z]*$", word) or re.match(r"^[0-9\/\:\-]+$", word) or 
            re.match(r"^[A-Za-z]+[0-9]{1, 3}[A-Za-z]*$", word) or 
            re.match(r"(\w+(\:\/\/))?([\w\-]+\.)?[\w\-]+\.[\w\-]+[\/\w\+-\?\{\}\(\)\[\]\&\^\$\#\@\~]*", word)) 
            and re.match(r"[A-Za-z0-9]", word)):
            return True

        return False

    '''
    @input: Raw text without any bigram symbol
    @output: Text with added required symbols
    @description:
    Step 1: Replace all representations of dates with |DATE|
    Step 2: Replace all representations of times with |TIME|
    Step 3: Replace all representations of links with |URL|
    Step 4: Replace all representations of numbers with |NUMBER|
    Step 5: Add |START_SENT| to the beginning of each sentence
    Step 6: Add |END_SENT| to the end of each sentence
    '''
    def impute_bigram_symbols(self, text):
        text = self.replace_dates(text)
        text = self.replace_times(text)
        text = self.replace_urls(text)
        text = self.replace_numbers(text)

        sentences = [self.customized_symbols['sent_start'] + " " + 
            re.sub(r"(\n+)|(\s+)", ' ', sentence.strip()) + " " + self.customized_symbols['sent_end']
            for sentence in sent_tokenize(text) if len(re.sub(r"(\n+)|(\s+)", ' ', sentence.strip())) > 5]
        
        return "\n".join(sentences)

    def replace_dates(self, text, replace_with = None):
        text = re.sub(r"\b\d{1,2}(\/|\-|\_|\s)\d{1,2}(\/|\-|\_|\s)(\d{4}|\d{2})\b", 
            self.customized_symbols['date'], text)
        text = re.sub(r"\d{1,2}(\s*)(jan|feb|mar|apr|may|jun|jul|aug|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)(\s*)(\d{4}|\d{2})", 
            self.customized_symbols['date'], text, flags=re.IGNORECASE)
        text = re.sub(r"(jan|feb|mar|apr|may|jun|jul|aug|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)(\s|\s?\,\s?)?\d{1,2}(st|nd|rd|th)?(\s|\s?\,\s?)?(\d{4}|\d{2})", 
            self.customized_symbols['date'], text, flags=re.IGNORECASE)

        return text

    def replace_times(self, text, replace_with = None):
        replace_with = self.customized_symbols['time'] if replace_with == None else replace_with

        text = re.sub(r"\d{1,2}(\s*(am|pm)|(\:|\-)\d{2}(\s*(am|pm)|(\:|\-)\d{2}(\s*(am|pm))?))", 
            replace_with, text, flags=re.IGNORECASE)

        return text

    def replace_urls(self, text, replace_with = None):
        replace_with = self.customized_symbols['url'] if replace_with == None else replace_with

        text = re.sub(r"(\w+(\:\/\/))?([\w\-]+\.)?[\w\-]+\.[\w\-]+[\/\w\+-\?\{\}\(\)\[\]\&\^\$\#\@\~]*", 
            replace_with, text, flags=re.IGNORECASE)

        return text

    def replace_numbers(self, text, replace_with = None):
        replace_with = self.customized_symbols['number'] if replace_with == None else replace_with

        text = re.sub(r"(\d+(\.\d+|[,0-9]+(\.\d+)?)?)|(\.\d+)", 
            replace_with, text, flags=re.IGNORECASE)

        return text

    def is_customized_word(self, word):
        return word in self.customized_symbols.values()

    def fetch_line_words(self, line, escape_puncs = True, escape_symbols = True):
        separators = "\\".join([char for char in string.punctuation])
        separators = "^[\\" + separators + "]$"

        initial_words = word_tokenize(line)

        return pos_tag([word for word in initial_words if 
            (not escape_puncs or not re.match(separators, word)) and 
            (not escape_symbols or not self.is_customized_word(word))])

    def fetch_lemmatized_word(self, word, pos=''):
        wordnet_pos = self.get_wordnet_pos(pos.lower())

        if(wordnet_pos):
            root = self.lemmatizer.lemmatize(word.lower(), pos=wordnet_pos)
        else:
            root = self.lemmatizer.lemmatize(word.lower())

        return root

    def get_wordnet_pos(self, treebank_tag):
        if treebank_tag.startswith('j'):
            return wordnet.ADJ
        elif treebank_tag.startswith('v'):
            return wordnet.VERB
        elif treebank_tag.startswith('n'):
            return wordnet.NOUN
        elif treebank_tag.startswith('r'):
            return wordnet.ADV
        else:
            return ''
        