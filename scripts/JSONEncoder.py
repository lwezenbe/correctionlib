#! /usr/bin/env python3
# Author: Izaak Neutelings (March 2022)
# Description: Reduce number of lines in JSON by collapsing lists
# Adapted from:
#   https://stackoverflow.com/questions/13249415/how-to-implement-custom-indentation-when-pretty-printing-with-the-json-module
#   https://stackoverflow.com/questions/16264515/json-dumps-custom-formatting
import json


class JSONEncoder(json.JSONEncoder):
  """
  Encoder to make correctionlib JSON more compact:
  - keep list of primitives (int, float, str) on one line
  - do not break line for simple CategoryItem dictionary if value is primitive
  - do not break line for first key of dictionary
  """
  
  def __init__(self, *args, **kwargs):
    super(JSONEncoder,self).__init__(*args, **kwargs)
    self.current_indent = 0
    self.current_indent_str = ""
    self.nobreak = True # for first key in dict
  
  def encode(self, obj):
    # Special Processing for lists of primitives
    if isinstance(obj,(list,tuple)):
      output = [ ]
      #if not any(isinstance(x,(list,tuple,dict)) for x in obj):
      if all(isinstance(x,(int,float,str)) for x in obj): # primitives
        for item in obj:
          output.append(json.dumps(item))
        return "[ "+", ".join(output)+" ]"
      else:
        self.current_indent += self.indent
        self.current_indent_str = "".join([" " for x in range(self.current_indent)])
        for item in obj:
          output.append(self.current_indent_str+self.encode(item))
        self.current_indent -= self.indent
        self.current_indent_str = "".join([" " for x in range(self.current_indent)])
        return "[\n"+",\n".join(output)+"\n"+self.current_indent_str+"]"
    elif isinstance(obj,dict):
      output = [ ]
      if len(obj)==2 and all(isinstance(obj[k],(int,float,str)) for k in obj):
        return "{ "+", ".join(json.dumps(k)+": "+self.encode(obj[k]) for k in obj)+" }"
      else:
        self.current_indent += self.indent
        self.current_indent_str = "".join([" " for x in range(self.current_indent)])
        first = self.nobreak
        for key, value in obj.items():
          if first and not isinstance(value,(list,tuple,dict)): # no break on first
            row = ' '*(self.indent-1)+json.dumps(key)+": "+self.encode(value)
          else:
            self.nobreak = not isinstance(value,dict) # no break on first
            row = '\n'+self.current_indent_str+json.dumps(key)+": "+self.encode(value)
            self.nobreak = True
          output.append(row)
          first = False
        self.current_indent -= self.indent
        self.current_indent_str = "".join([" " for x in range(self.current_indent)])
        return "{"+",".join(output)+"\n"+self.current_indent_str+"}"
    return json.dumps(obj)
    

def write(corr,fname,indent=2):
  with open(fname,'w') as fout:
    fout.write(corr.json(exclude_unset=True,cls=JSONEncoder,indent=indent))
  

if __name__ == '__main__':
  data = { # quick test of JSONEncoder behavior
    'layer1': {
      'layer2': {
        'layer3_1': [{"x":1,"y":7}, {"x":0,"y":4}, {"x":5,"y":3},
                     {"x":6,"y":9}, {'key': 'foo', 'value': 1},
                     {'key': 'foo', 'value': {k: v for v, k in enumerate('abcd')}},
                     {k: v for v, k in enumerate('abc')},
                     {k: {k2: v2 for v2, k2 in enumerate('ab')} for k in 'ab'}],
        'layer3_2': 'string',
        'layer3_3': [{"x":2,"y":8,"z":3}, {"x":1,"y":5,"z":4},
                     {"x":6,"y":9,"z":8}],
        'layer3_4': list(range(20)),
        'layer3_5': ['a','b','c'],
      }
    }
  }
  print(json.dumps(data,cls=JSONEncoder,sort_keys=True,indent=2))
  
