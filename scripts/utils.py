#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with different formats, writing, reading, evaluating and validating.
# Instructions:
#  ./scripts/test.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
#   https://stackoverflow.com/questions/13249415/how-to-implement-custom-indentation-when-pretty-printing-with-the-json-module
import os, sys; sys.path.append('src')
assert sys.version_info>=(3,8),"Python version must be newer than 3.8, currently %s.%s"%(sys.version_info[:2])
import correctionlib._core as core
import correctionlib.schemav2 as schema
import correctionlib.JSONEncoder as JSONEncoder
from correctionlib.schemav2 import Correction, CorrectionSet
import json, jsonschema


def getsystinfo():
  """Help function to create description of systematic inputs."""
  return "Systematic variation: 'nom', 'up', 'down'"
  
def getgminfo():
  """Help function to create description of genmatch inputs."""
  return "genmatch: 0 or 6 = unmatched or jet, 1 or 3 = electron, 2 or 4 = muon, 5 = real tau"
  
def getdminfo(dms):
  """Help function to create description of DM inputs."""
  dminfo = ', '.join(str(d) for d in dms)
  return f"Reconstructed tau decay mode: {dminfo}"
  
def getwpinfo(id,wps):
  """Help function to create description of WP inputs."""
  try:
    wpmin = max([w for w in wps if 'loose' in w.lower()],key=lambda x: len(x)) # get loose WP with most 'V's
    wpmax = max([w for w in wps if 'tight' in w.lower()],key=lambda x: len(x)) # get tight WP with most 'V's
    info  = f"{id} working point: {wpmin}-{wpmax}"
  except:
    info  = f"{id} working point: {', '.join(wps)}"
  return info
  

def wp_sortkey(string):
  """Help function to sort WPs. Use as
      wps = ['Medium','Tight','Loose','VTight','VLoose','VVTight']
      sorted(wps,key=wp_sortkey)
  """
  lowstr = string.lower()
  if lowstr.startswith('medium'):
    return 0
  elif lowstr.lstrip('v').startswith('loose'):
    return -1*(lowstr.count('v')+1)
  elif lowstr.startswith('tight'):
    return 1*(lowstr.count('v')+1)
  return 100+len(string) # anything else at the end
  

def header(string):
  print("\n>>> \033[1m\033[4m%s\033[0m"%(string))
  
def warn(string):
  return ">>> "+f"\033[33m{string}\033[0m"
  

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
  

def ensuredir(dirname,**kwargs):
  """Make directory if it does not exist."""
  verbosity = kwargs.get('verb',  0    )
  if not os.path.exists(dirname):
    os.makedirs(dirname)
    if verbosity>=1:
      print(f'>>> Made directory "{dirname}"')
    if not os.path.exists(dirname):
      print(f'>>> Failed to make directory "{dirname}"')
  return dirname


