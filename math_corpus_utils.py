import re
from num2words import num2words
from cleantext import clean 
import contractions # for expanding contractions
import nltk
from nltk.tokenize.punkt import PunktSentenceTokenizer
import spacy
from spacy import displacy

sent_tokenizer = lambda s: PunktSentenceTokenizer().tokenize(s)
expand_contract = lambda s: ' '.join([ contractions.fix(word) for word in s.split()])

def number_to_words(num):
    try:
        return num2words(re.sub(",", "", num))
    except:
        return num

basic_clean = lambda s: clean(s,
                              fix_unicode=True,               # fix various unicode errors
                              to_ascii=True,                  # transliterate to closest ASCII representation
                              lower=True,                     # lowercase text
                              no_line_breaks=True,           # fully strip line breaks as opposed to only normalizing them
                              no_urls=True,                  # replace all URLs with a special token
                              no_emails=True,                # replace all email addresses with a special token
                              no_phone_numbers=True,         # replace all phone numbers with a special token
                              no_numbers=False,               # replace all numbers with a special token
                              replace_with_number= lambda m: number_to_words(m.group()), # replace number with words

                              no_digits=False,                # replace all digits with a special token
                              no_punct=False,                 # DO NOT remove punctuations
                             #replace_with_punct="",          # instead of removing punctuations you may replace them
    
                              no_currency_symbols=True,      # replace all currency symbols with a special token
                            # what do I do with dollar signs right now?
                              replace_with_currency_symbol="", 
                              lang="en"                       
                            )

def normalize_math_symbol(s):
    if r'\frac' in s:             # use 1/2 to represent \frac{1}{2} or convert to words
        s = re.sub(r'\\frac\s?\{','', s.replace('}{','/'))
    if r'\div' or '÷' in s:       # Q: change to divided by??
        s = re.sub(r'\\div|÷','divided by', s)
    if r'\times' or '×' in s:     # Q: change it to times or multiply by??
        s = re.sub(r'\\times|×','times',s)
    ## DO WE WANT TO KEEP symbols of + - = > < ?
    # if '+' in s:
    #   s = s.replace('+','plus')
    # if r'-' in s:
    #   s = s.replace('-','minus')
    return re.sub(r'[\\\(\)\{\}\[\]]+','',s) # remove useless symboles like \, (,),{,},[,]

NER = spacy.load("en_core_web_sm")
def ner_normalization(s):
  text = NER(s) # train spacy NER model on text
  processed_tokens = []
  for token in text:
    if token.ent_type_ in ['ORG','PRODUCT','GPE','LOC']:
      processed_tokens.append('<entity>') # Replace entities with arbitrary token
    else:
      processed_tokens.append(token.text)
  return ' '.join(processed_tokens) # text with entity normalization

def text_cell_clean(text):
  # 1. basic cleaning
  clean_txt = basic_clean(text)
  # 2. expand contractions 
  expand_txt = expand_contract(clean_txt)
  # 3. normalize math symbols
  nor_txt = normalize_math_symbol(expand_txt)
  # 4. sentence tokenization
  sentences = sent_tokenizer(nor_txt)
  return sentences