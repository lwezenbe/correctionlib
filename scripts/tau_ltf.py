#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with format of TauPOG SFs.
# Instructions:
#  ./scripts/test.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html#Tau
import sys; sys.path.append('scripts')
from utils import *


def test_ltf(corrs,ltype='e'):
  """e -> tauh fake rate SF"""
  header(f"{ltype} -> tauh fake rate SF")
  if 'e' in ltype: # e -> tauh
    fname = "data/tau/tau_etf.json"
    ebins = [0.0,1.460,1.558,2.3] # eta bins
    gm    = 1 # genmatch
    gms   = [1,3]
  else: # mu -> tauh
    ltype = "mu"
    fname = "data/tau/tau_mtf.json"
    ebins = [0.0,0.4,0.8,1.2,1.7,2.3] # eta bins
    gm    = 2 # genmatch
    gms   = [2,4]
  allgms = [1,2,3,4,5,6,0] # all allowed genmatches
  nsfs   = len(ebins)-1
  wps    = [
    #'VVVLoose', 'VVLoose', 'VLoose',
    'Loose', 'Medium', 'Tight',
    #'VTight', 'VVTight'
  ]
  sfs   = {wp: [(1.0,1.1,0.9) for s in range(nsfs)] for wp in wps}
  print(ebins,sfs)
  
  # LTF DATA
  ltfdata = {
    'nodetype': 'category', # category:wp
    'input': "wp",
    'content': [ # key:wp
      { 'key': wp, # key:wp==wp
        'value': {
          'nodetype': 'transform', # transform:eta
          'input': "eta",
          'rule': {
            'nodetype': 'formula',
            'expression': "abs(x)",
            'parser': "TFormula",
            'variables': ["eta"],
          },
          'content': {
            'nodetype': 'binning', # binning:eta
            'input': "eta",
            'edges': ebins,
            'flow': "clamp", # do
            'content': [ # bin:eta
              { 'nodetype': 'category', # category:syst
                'input': "syst",
                'content': [ # key:syst
                  { 'key': 'nom',  'value': bin[0] }, # central
                  { 'key': 'up',   'value': bin[1] }, # up
                  { 'key': 'down', 'value': bin[2] }, # down
                ] # key:syst
              } for bin in sfs[wp]
            ] # bin:eta
          } # binning:eta
        } # transform:eta
      } for wp in wps # key:wp==wp
    ] # key:wp
  } # category:wp
  
  # CORRECTION OBJECT
  corr  = Correction.parse_obj({
    'version': 0,
    'name': f"DeepTau2017v2p1VS{ltype}_test",
    'description': f"{ltype} -> tau_h fake rate SFs for DeepTau2017v2p1VS{ltype}",
    'inputs': [
      {'name': "eta",      'type': "real",   'description': "tau eta"},
      {'name': "genmatch", 'type': "int",    'description': "genmatch (0 or 6: no match or jet, 1 or 3: electron, 2 or 4: muon, 5: real tau"},
      {'name': "wp",       'type': "string", 'description': f"DeepTauVSe WP: {wps[0]}-{wps[-1]}"},
      {'name': "syst",     'type': "string", 'description': "systematic: 'nom', 'up', 'down'"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:genmatch -> category:wp -> transform:eta -> binning:eta -> category:syst
      #'nodetype': 'transform', # transform:eta
      #'input': "genmatch",
      #'rule': {
      #  'nodetype': 'category', # category:genmatch
      #  'input': "genmatch",
      #  'default': 0, # everything else
      #  'content': [ # key:genmatch
      #    { 'key': gm,   'value': gm }, # l -> tau_h, prompt
      #    { 'key': gm+2, 'value': gm }, # l -> tau_h, tau decay
      #  ] # key:genmatch
      #}, # category:genmatch
      #'content': {
        'nodetype': 'category', # category:genmatch
        'input': "genmatch",
        #'default': 1.0, # no default: throw error if unrecognized genmatch
        'content': [ # key:genmatch
          { 'key': gm,
            'value': ltfdata if gm in gms else 1.0
          } for gm in allgms
        ] # key:genmatch
    } # category:genmatch
    #} # transform:genmatch
  })
  print(corr)
  #print(corr.data.content)
  print(f">>> Writing {fname}...")
  JSONEncoder.write(corr,fname)
  corrs.append(corr)
  

def evaluate(corrs):
  header("Evaluate")
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  etabins = [-2.0,-1.0,0.0,1.1,2.0,2.5,3.0]
  gms     = [0,1,2,3,4,5,6,7]
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    wp   = 'Tight'
    print(f">>>\n>>> WP={wp}")
    print(">>> %8s"%("genmatch")+" ".join("  %-15.1f"%(e) for e in etabins))
    for gm in gms:
      row = ">>> %8d"%(gm)
      for eta in etabins:
        sfnom = 0.0
        for syst in ['nom','up','down']:
          #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
          try:
            sf = corr.evaluate(eta,gm,wp,syst)
            if 'nom' in syst:
              row += "%6.2f"%(sf)
              sfnom = sf
            elif 'up' in syst:
              row += "%+6.2f"%(sf-sfnom)
            else:
              row += "%+6.2f"%(sf-sfnom)
          except Exception as err:
            row += "\033[1m\033[91m"+"  ERR".ljust(6)+"\033[0m"
      print(row)
  print(">>>")
  

def main():
  corrs = [ ] # list of corrections
  test_ltf(corrs,'e')
  test_ltf(corrs,'m')
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()

