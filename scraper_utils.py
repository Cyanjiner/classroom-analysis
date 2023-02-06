import pandas as pd
import glob, re, os, copy
import numpy as np
import docx

"""
for Talk Math Corpus
"""

def read_full_doc(dir):
    with open(dir, "r") as file:
        doc = file.read()
    return doc

def extract_paren_substring(string):
    """
    extracted substrings within the parentheses
    ------
    returns a pair of substrings (substrings without content in (), substrings within ())
    """
    start = string.index("(")
    end = string.index(")")
    substring = string[start+1:end]
    return string.replace('('+ substring + ')', ""), substring

def split_grade_section(lesson_text):
  grade_content = re.split(r"(Grade K+|Grade \d+)", lesson_text)[1:]
  grade_dict = {}
  for j in range(len(grade_content)):
    g_content = grade_content[j]
    if j % 2 == 0: # even index --> grade_content[j] is the separator
      index = grade_content[j]
      #g_text = grade_content[j+1].strip().split('\n')
      g_text = re.sub(r'\s+', ' ', grade_content[j+1])
      g_text = re.sub('Talking Math','', g_text)
      text_list = re.split(r'(?<=[.!?]\s)+',g_text) # split by punctuation characters
      # filtering out empty string & any element w/ "Talking Math" from the g_text list
      text_list = list(filter(None, text_list))
      #get standard if there is one
      for i in range(len(text_list)):
         if  '(' and ')' in text_list[i]:
           new_s, standard = extract_paren_substring(text_list[i])
           text_list[i] = new_s
         else:
           standard = 'NA'
         result = {'standard': standard, "text": [text for text in text_list if text.strip()]}

      grade_dict[index] = result
      #grade_dict[index] = grade_content[j+1]
  return grade_dict

def split_lesson_section(doc):
    main_section = re.split(r"(Invitational \d+|Day \d+)", doc)
    lesson = []
    text = []
    for i, content in enumerate(main_section[1:]):
        if i % 2 != 0: 
            lesson_text = content # if even index --> content is the text follows by lesson
            grade_dict = split_grade_section(lesson_text)
            text.append(grade_dict)
        else: # if odd index --> content is the separator (i.e. lesson index)
            lesson_name = content
            lesson.append(lesson_name)
    return {'lesson': lesson, "text": text}

def dict_to_df(d):
    n = len(d['lesson'])
    talk_math_dict = []
    for i in range(n):
        lesson_index = d['lesson'][i]
        grade_dict = d['text'][i]
        for grade, values in grade_dict.items():
            grade_name = grade.split(" ")[1]
            standard = values['standard']
            text = values['text']
            talk_math_dict.append({
                'grade': grade_name, 
                'lesson':lesson_index, 
                'standard': standard, 
                'text': text})
    return pd.DataFrame(talk_math_dict)


"""
for EngageNY materials
"""

## For the entire dataset
cols_for_df = ['grade','module','topic','lesson','objective',
               'lesson_part','standard','text_type','text',
               'subject','path','material',]
lesson_df = pd.DataFrame(columns = cols_for_df)


def extract_lesson_text(fileinfo):
  '''This function takes in a dictionary containing the file information 
  created from parsing glob (see below). From this, it parses .docx
  documents by file path, extracts relevant pieces, and stores them in a 
  dataframe.
  The files are from the publicly available engageNY curricula found here:
  https://nysed.sharepoint.com/sites/P12EngageNY-Math-EXTA/Shared%20Documents/Forms/AllItems.aspx?ga=1&id=%2Fsites%2FP12EngageNY%2DMath%2DEXTA%2FShared%20Documents%2FMathematics&viewid=74a2b97e%2D3088%2D44b7%2Dab73%2D420870c488b4
  

      Inputs: dictionary 
      Returns: DataFrame w extracted text info
  '''
  grade = fileinfo['grade']
  module = fileinfo['module']
  topic = fileinfo['topic']
  lesson = fileinfo['lesson']
  path = fileinfo['path']
  material = fileinfo['material']
  subject = fileinfo['subject']
  document = docx.Document(path)
  all_text = []
  for para in document.paragraphs:
      all_text.append(para.text.split('\t'))  

  lesson_df = pd.DataFrame(columns = cols_for_df)
  new_df = pd.DataFrame(columns = cols_for_df)
  prev_df = pd.DataFrame(columns = cols_for_df)
  curr_obj,prev_objective,curr_lesson_part,prev_lesson_part,curr_std,prev_std = ['None'] *6

  curr_lesson_tags = {}
  ts_convo = []
  other_txt = []
  prev_ts_convo = []
  prev_other = []
  prev_text = []
  prev_type, curr_type = ["overview"]*2
  curr_text = []
  for txt_list in all_text:
    if '' in txt_list:
      txt_list.remove('')

    if (txt_list == ['']) or (txt_list==[]) or not txt_list:
      pass

    elif "Objective:" in txt_list[0]:
      curr_obj = txt_list[0].split("  ")[-1].strip()

    elif ' minutes)' in txt_list[-1] and len(txt_list)>1:
      if txt_list[0].split("  ")[-1].strip() in list(sdf.standard_code):
        tmp = [x.strip() for x in txt_list[0].split("  ")]
        standards = tmp[-1]
        lesson_parts = " ".join(tmp[:-1])
        curr_lesson_tags[lesson_parts] = standards 

    elif ' minutes)' in txt_list[0]: 

      curr_lesson_part = txt_list[0].split("  ")[0].strip()
      if curr_lesson_part in curr_lesson_tags.keys():
        if curr_lesson_tags[curr_lesson_part] == 'None':
          curr_lesson_tags[curr_lesson_part] = prev_std
        curr_std = curr_lesson_tags[curr_lesson_part]
      else:
        curr_lesson_tags[curr_lesson_part] = curr_std

    else:
      if 'T:' in txt_list or 'S:' in txt_list or 'T: ' in txt_list or 'S: ' in txt_list:
        curr_type = 'ts_dialogue'
      elif any([re.search(r"^\s{0,2}Problem \d{1,2}",x) for x in txt_list]) or curr_lesson_part in ['Exit Ticket'] or ((prev_type == 'problems') and ((1== len(prev_text)) or (any(['?' in x for x in txt_list])))):
        curr_type = 'problems'
      elif any(['?' in x for x in txt_list]) or any(['Debrief' in x for x in txt_list]):
        curr_type = 'ts_dialogue'
      elif ":" in txt_list[0].split("  ")[0]:
        curr_type = 'instructional_guidance'
      else: 
        curr_type = prev_type
      if prev_type == curr_type and curr_lesson_part == prev_lesson_part:
        curr_text.append(txt_list)
      else: 
        curr_text = [copy.deepcopy(txt_list)]

      if (curr_lesson_part != 'None') and txt_list != ['']:
        new_df = pd.DataFrame({'grade':grade,'module':module,
                              'topic':topic,'lesson':lesson,
                              'objective':curr_obj,
                              'lesson_part':curr_lesson_part,
                              'standard':curr_std,
                              'text_type':curr_type,
                              'text':[copy.deepcopy(curr_text)],
                               'subject':subject,
                               'path':path,
                               "material":material,
                               })
        if prev_type != curr_type:
          lesson_df = pd.concat([lesson_df,prev_df])

    prev_objective = curr_obj
    prev_std = curr_std
    prev_lesson_part = curr_lesson_part
    prev_ts_convo = copy.deepcopy(ts_convo)
    prev_text = copy.deepcopy(curr_text)
    prev_df = copy.deepcopy(new_df)
    prev_type = curr_type
    
  lesson_df = pd.concat([lesson_df,prev_df])
  return lesson_df
    

def save_engageny_df(root_dir, data_dir):
    files = {}
    for name in glob.iglob(root_dir + data_dir + "**/*lesson*.docx", recursive=True):
        doc = name.split("/")[-1][:-5]
        filename = doc.split("-")
        if len(filename) >= 7 and filename[0][0] not in ["~","$"]:
            subj, grade, module, top, topic,ls,lesson = filename[:7]
            material = filename[-1]
            files[doc] = {"path":name,
                        "subject":subj,
                        "grade":grade[-1],
                        "module":module,
                        "topic":topic,
                        "lesson":lesson,
                        "material":material,
                        }

    for d, info in files.items():
        lesson_df = pd.concat([lesson_df,extract_lesson_text(info)])
    lesson_df.to_csv(root_dir + data_dir + "full_lesson_text_extra_grades.csv")
    return lesson_df