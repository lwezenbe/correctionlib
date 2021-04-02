#! /usr/bin/env python3
# Author: Izaak Neutelings (April 2021)
# Description: Script to test integer mapping.
# Instructions:
#  ./scripts/test_mapping.py
import sys; sys.path.append('scripts')
from utils import *


def makecorr_map():
  """Mapping integers"""
  corr  = Correction.parse_obj({
    'version': 0,
    'name': "Mapping",
    'description': "Mapping integers",
    'inputs': [
      {'name': "dm", 'type': "int", 'description': "Tau decay mode"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # transform:dm -> category:dm -> float:SF
      'nodetype': 'transform', # transform:eta
      'input': "dm",
      'rule': {
        'nodetype': 'category', # category:dm
        'input': "dm",
        'default': -1, # map everything else onto 0
        'content': [ # key:dm
          { 'key':  0, 'value':  0 },
          { 'key':  1, 'value':  1 },
          { 'key': 10, 'value': 10 },
          { 'key': 11, 'value': 10 }, # map 11 -> 10
        ] # key:dm
      }, # category:dm
      'content': {
        'nodetype': 'category', # category:dm
        'input': "dm",
        #'default': -1.0, # no default: throw error if unrecognized dm
        'content': [ # key:dm
          { 'key': -1, 'value': -1.00 },
          { 'key':  0, 'value':  1.00 },
          { 'key':  1, 'value':  1.01 },
          { 'key': 10, 'value':  1.10 },
          { 'key': 11, 'value':  1.11 },
        ] # key:dm
      } # category:dm
    } # transform:dm
  })
  print(JSONEncoder.dumps(corr))
  return corr
  

def evaluate(corrs):
  header("Evaluate")
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  dms   = [0,1,2,10,11]
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    print(">>> %6s %8s"%("dm","sf"))
    for dm in dms:
      row = ">>> %6d"%(dm)
      try:
        sf = corr.evaluate(dm)
        row += " %8.2f"%(sf)
      except Exception as err:
        row += "\033[1m\033[91m"+err+"\033[0m"
      print(row)
  print(">>>")
  

def main():
  corr1 = makecorr_map()
  corrs = [corr1] # list of corrections
  evaluate(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
