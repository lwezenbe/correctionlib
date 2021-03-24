#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with different formats, writing, reading, evaluating and validating.
# Instructions:
#  ./scripts/test.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
#   https://stackoverflow.com/questions/13249415/how-to-implement-custom-indentation-when-pretty-printing-with-the-json-module
import sys; sys.path.append('src')
assert sys.version_info>=(3,8),"Python version must be newer than 3.8, currently %s.%s"%(sys.version_info[:2])
import correctionlib._core as core
import correctionlib.schemav2 as schema
from correctionlib.schemav2 import Correction, CorrectionSet
import json, jsonschema
import JSONEncoder


def header(string):
  print("\n>>> \033[1m\033[4m%s\033[0m"%(string))
  

def eval(corr,*args):
  try:
    sf = "%.1f"%(corr.evaluate(*args))
  except Exception as err:
    sf = f" \033[1m\033[91m{err.__class__.__name__}\033[0m\033[91m: {err}\033[0m"
  return sf
  

def wrap(corrs):
  """Return purely python CorrectionSet object, and wrapped C++ CorrectionSet object."""
  cset_py = schema.CorrectionSet( # simple python CorrectionSet object
    schema_version=schema.VERSION,
    corrections=list(corrs),
  )
  cset_cpp = core.CorrectionSet.from_string(cset_py.json()) # wrap to create C++ object that can be evaluated
  return cset_py, cset_cpp
  
