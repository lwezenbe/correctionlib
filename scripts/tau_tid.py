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


def maketid(sfs,ibin,syst='nom'):
  """Interpolate."""
  # f = TFormula('f',sf)
  # for x in [10,20,29,30,31,35,45,100,200,499,500,501,750,999,1000,1001,1500,2000]: x, f.Eval(x)
  # "x<20?0: x<25?1.00: x<30?1.01: x<35?1.02: x<40?1.03: 1.04"
  # "x<20?0: x<25?1.10: x<30?1.11: x<35?1.12: x<40?1.13: x<500?1.14: x<1000?1.04+0.2*x/500.: 1.44"
  # "x<20?0: x<25?0.90: x<30?0.91: x<35?0.92: x<40?0.93: x<500?0.94: x<1000?1.04-0.2*x/500.: 0.64"
  if syst=='nom':
    sf = sfs[ibin][0]
  else:
    sfnom, sfup, sfdown = sfs[ibin]
    if ibin<5: # pt < 500
      sf = sfnom-sfdown if syst=='down' else sfnom+sfup
    elif ibin==5: # 500 < pt < 1000
      sf = "%.6g-%.6g*x"%(sfnom,sfdown/500.) if syst=='down' else "%.6g+%.6g*x"%(sfnom,sfup/500.)
      sf = { # linearly inflate uncertainty x2
        'nodetype': 'formula', # pT-dependent
        'expression': sf,
        'parser': "TFormula",
        'variables': ["pt"],
      }
    else: # pt > 1000
      sf = sfnom-2*sfdown if syst=='down' else sfnom+2*sfup # inflate uncertainty x2
  print(sf)
  #if syst=='down': exit(0)
  return sf
  

def test_tid_pt(corrs):
  """Tau ID SF, pT-dependent."""
  header("Tau DeepTauVSjet SF, pT-dependent")
  fname   = "data/tau/tau_tid.json"
  dms     = [
    0, 1, 10, 11
  ]
  wps     = [
    #'VVVLoose', 'VVLoose', 'VLoose',
    'Loose', 'Medium', 'Tight',
    #'VTight', 'VVTight'
  ]
  ptbins  = [20.,25.,30.,35.,40.,500.,1000.,2000.]
  nptbins = len(ptbins)-1
  sfs     = {wp: [(1.,0.2,0.2) for i in range(nptbins)] for wp in wps}
  corr    = Correction.parse_obj({
    'version': 0,
    'name':    "test_DeepTau2017v2p1VSjet",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "tau pt"},
      #{'name': "dm",       'type': "int",    'description': "tau decay mode (0, 1, 10, or 11)"},
      {'name': "genmatch", 'type': "int",    'description': "genmatch (0 or 6: no match, jet, 1 or 3: electron, 2 or 4: muon, 5: real tau"},
      {'name': "wp",       'type': "string", 'description': "DeepTauVSjet WP: VVVLoose-VVTight"},
      {'name': "syst",     'type': "string", 'description': "systematic 'nom', 'up', 'down'"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:genmatch -> category:wp -> transform:eta -> binning:eta -> category:syst
      'nodetype': 'category', # category:genmatch
      'input': "genmatch",
      'default': 1.0, # default TES if unrecognized genmatch
      'content': [
        { 'key': 5,
          'value': {
            'nodetype': 'category', # category:wp
            'input': "wp",
            'default': 1.0, # default TES if unrecognized genmatch
            'content': [
              { 'key': wp,
                'value': {
                  'nodetype': 'binning',
                  'input': "pt",
                  'edges': ptbins,
                  'flow': "clamp",
                  'content': [
                    { 'nodetype': 'category', # syst
                      'input': "syst",
                      'content': [
                        { 'key': 'nom',  'value': maketid(sfs[wp],i,'nom')  },
                        { 'key': 'up',   'value': maketid(sfs[wp],i,'up')   },
                        { 'key': 'down', 'value': maketid(sfs[wp],i,'down') },
                      ]
                    } for i in range(nptbins)
                  ]
                }
              } for wp in wps
            ]
          } # category:wp
        }
      ]
    } # category:genmatch
  })
  print(corr)
  print(corr.data.content)
  print(f">>> Writing {fname}...")
  with open(fname,'w') as fout:
    fout.write(corr.json(exclude_unset=True,indent=2))
  corrs.append(corr)
  

def evaluate(corrs):
  header("Evaluate")
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  ptbins = [10.,21.,26.,31.,36.,41.,501.,750.,999.,2000.]
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    wps = ['Medium','Tight']
    for wp in wps:
      print(f">>>\n>>> WP={wp}")
      print(">>> %8s"%("genmatch")+" ".join("  %-15.1f"%(p) for p in ptbins))
      for gm in [0,1,2,3,4,5,6]:
        row = ">>> %8d"%(gm)
        for pt in ptbins:
          sfnom = 0.0
          for syst in ['nom','up','down']:
            #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
            try:
              sf = corr.evaluate(pt,gm,wp,syst)
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
  test_tid_pt(corrs)
  #test_tid_dm(corrs)
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
