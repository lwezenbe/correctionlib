#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with different formats, writing, reading, evaluating and validating.
# Instructions:
#  ./scripts/test.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
import sys; sys.path.append('scripts')
from utils import *


def test_hist1D(corrs):
  header("Hist1D SFs")
  xbins = [0.0,1.1,2.5]
  nsfs  = len(xbins)-1
  sfs   = [float(s) for s in range(nsfs)]
  print(xbins,sfs)
  print(">>> Under-/Overflow throws error")
  corr1 = Correction.parse_obj({
    'version': 0,
    'name': "test_hist1D",
    'description': "Simple 1D SF",
    'inputs': [
      {'name': "eta", 'type': "real", 'description': "tau eta"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "binning",
      'input': "eta",
      'edges': xbins,
      'flow': "error", # throw error if input out of bounds
      'content': sfs,
    },
  })
  print(corr1)
  print(corr1.data.content)
  #help(corr1)
  print(">>> Under-/Overflow clamps")
  corr2 = Correction.parse_obj({
    'version': 0,
    'name': "test_hist1D_clamp",
    'description': "Simple 1D SF with clamp",
    'inputs': [
      {'name': "eta", 'type': "real", 'description': "tau eta"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "binning",
      'input': "eta",
      'edges': xbins,
      'flow': "clamp", # use adjacent bin for under-/overflow
      'content': sfs,
    },
  })
  print(corr2)
  print(">>> Transformation")
  corr3 = Correction.parse_obj({
    'version': 0,
    'name': "test_hist1D_transform",
    'description': "Simple 1D SF with transformation eta = abs(eta)",
    'inputs': [
      {'name': "eta", 'type': "real", 'description': "tau eta"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "transform",
      'input': "eta",
      #'rule': 1.0,
      'rule': {
        'nodetype': 'formula',
        'expression': "abs(x)",
        'parser': "TFormula",
        'variables': ["eta"],
        #'parameters': None,
      },
      'content': {
        'nodetype': "binning",
        'input': "eta",
        'edges': xbins,
        'flow': "error", # throw error if input out of bounds
        'content': sfs,
      },
    },
  })
  print(corr3)
  corrs.append(corr1)
  corrs.append(corr2)
  corrs.append(corr3)
  

def test_hist2D(corrs):
  header("Hist2D SFs")
  xbins = [0.0,1.1,2.5]
  ybins = [20.0,50.0,100.0,200.]
  nsfs  = (len(xbins)-1)*(len(ybins)-1)
  sfs1  = [float(s) for s in range(nsfs)]
  sfs2  = [[float((len(ybins)-1)*i+s) for s in range(len(ybins)-1)] for i in range(len(xbins)-1)]
  print(">>> Under-/Overflow throws error")
  print(xbins,ybins,sfs1)
  corr1 = Correction.parse_obj({
    'version': 0,
    'name': "test_hist2D",
    'description': "Simple 2D SF",
    'inputs': [
      {'name': "eta", 'type': "real", 'description': "tau eta"},
      {'name': "pt",  'type': "real", 'description': "tau pt"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "multibinning",
      'inputs': ["eta","pt"],
      'edges': [ xbins, ybins ],
      'flow': 'error', # throw error if input out of bounds
      'content': sfs1,
    },
  })
  print(corr1)
  print(">>> Under-/Overflow clamps")
  print(xbins,ybins,sfs2)
  corr2 = Correction.parse_obj({
    'version': 0,
    'name': "test_hist2D_clamp",
    'description': "Simple 2D SF with clamp",
    'inputs': [
      {'name': "eta", 'type': "real", 'description': "tau eta"},
      {'name': "pt",  'type': "real", 'description': "tau pt"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "binning",
      'input': "eta",
      'edges': xbins,
      'flow': "error", # throw error if input out of bounds
      'content': [{
        'nodetype': "binning",
        'input': "eta",
        'edges': ybins,
        'flow': "clamp", # use adjacent bin for under-/overflow
        'content': sfs2[i],
      } for i in range(len(xbins)-1)]
    },
  })
  print(corr2)
  corrs.append(corr1)
  corrs.append(corr2)
  

def test_category(corrs):
  header("Category SFs")
  keys    = [0,1,10,11]
  sfs     = { k: float(k) for k in keys }
  map     = { k: k for k in keys }
  map[11] = 10 # map 11 -> 10, dm -> dm otherwise
  print(">>> Default")
  corr1 = Correction.parse_obj({
    'version': 0,
    'name': "test_category",
    'description': "Simple category with default",
    'inputs': [
      {'name': "dm", 'type': "int", 'description': "decay mode"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "category",
      'input': "dm",
      'default': -9.,
      'content': [
        { 'key': k, 'value': sfs[k] } for k in keys
      ],
    },
  })
  print(corr1)
  print(">>> No default")
  corr2 = Correction.parse_obj({
    'version': 0,
    'name': "test_category_nodefault",
    'description': "Simple category with no default",
    'inputs': [
      {'name': "dm", 'type': "int", 'description': "decay mode"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "category",
      'input': "dm",
      'content': [
        { 'key': k, 'value': sfs[k] } for k in keys
      ],
    },
  })
  print(corr2)
  print(">>> Mapping")
  corr3 = Correction.parse_obj({
    'version': 0,
    'name': "test_category_mapping",
    'description': "Simple category with mapping 11 -> 10",
    'inputs': [
      {'name': "dm", 'type': "int", 'description': "decay mode"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': {
      'nodetype': "transform",
      'input': "dm",
      'rule': {
        'nodetype': 'category',
        'input': "dm",
        'default': -1,
        'content': [
          { 'key': k, 'value': map[k] } for k in keys
        ],
      },
      'content': {
        'nodetype': "category",
        'input': "dm",
        'default': -9.,
        'content': [
          { 'key': k, 'value': sfs[k] } for k in keys
        ],
      },
    },
  })
  print(corr3)
  corrs.append(corr1)
  corrs.append(corr2)
  corrs.append(corr3)
  

def test_formula(corrs):
  header("Formula SFs")
  exprs = [
    "x+1",
    "x*x", "x^2", "10^x",
    "sqrt(x)",
  ]
  for i, expr in enumerate(exprs):
    print(">>> Formula %r"%(expr))
    corr = Correction.parse_obj({
      'version': 0,
      'name': "test_formula%d"%(i),
      'description': "Simple formula, %r"%(expr),
      'inputs': [
        {'name': "p", 'type': "real", 'description': "variable"},
      ],
      'output': {'name': "weight", 'type': "real"},
      'data': {
        'nodetype': "formula",
        'expression': expr,
        'parser': "TFormula",
        'variables': ["p"],
      },
      #'data': Formula.parse_obj({
      #  'nodetype': "formula",
      #  'expression': "x*x",
      #  'parser': "TFormula",
      #  'variables': ["p"],
      #}),
    })
    print(corr)
    corrs.append(corr)
  

def write(corrs):
  header("Writing...")
  cset = CorrectionSet.parse_obj({
    'schema_version': schema.VERSION,
    'corrections': corrs,
  })
  for corr in corrs+[cset]:
    name  = corr.name if isinstance(corr,Correction) else "test_set"
    fname = "data/tau/%s.json"%(name)
    print(f">>>  Writing {fname}...")
    JSONEncoder.write(corr,fname)
    #with open(fname,'w') as fout:
    #  fout.write(corr.json(exclude_unset=True,indent=2))
  return cset
  

def read():
  header("Read & validate...")
  with open("data/tau/test_set.json") as fin:
    data = json.load(fin)
    out = jsonschema.validate(data,CorrectionSet.schema())
  print(type(data))
  print(data)
  #return cset
  

def evaluate(corrs):
  header("Evaluate")
  cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  #print([x.name for x in cset_py.corrections])
  #print([x for x in list(cset)])
  for name in list(cset):
    corr = cset[name]
    print(f">>> {name}: {corr.description}")
    if 'test_hist1D' in name:
      #print(corr.data.edges)
      for eta in [-2.0,-1.0,0.0,1.1,2.0,2.5,2.6]:
        print(">>>   eta=%4.1f, sf=%s"%(eta,eval(corr,eta)))
    elif 'test_hist2D' in name:
      for pt in [10.,20.,50.,80.,150.,250.]:
        for eta in [0.4,2.0,2.6]:
          print(">>>   eta=%4.1f, pt=%4.1f, sf=%4s"%(pt,eta,eval(corr,eta,pt)))
    elif 'test_category' in name:
      for key in [0,1,5,10,11]:
        print(">>>   key=%4s, sf=%4s"%(key,eval(corr,key)))
    elif 'test_formula' in name:
      for x in [-1.,0.,1.,2.,4.,10.]:
        print(">>>   x=%4s, sf=%4s"%(x,eval(corr,x)))
  

def main():
  corrs = [ ] # list of corrections
  test_hist1D(corrs)
  test_hist2D(corrs)
  test_category(corrs)
  test_formula(corrs)
  evaluate(corrs)
  write(corrs)
  read()
  

if __name__ == '__main__':
  main()
  print()
  
