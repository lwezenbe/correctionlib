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
from collections import namedtuple
TES = namedtuple('TES',['nom','uncup_lowpt','uncup_highpt','uncdn_lowpt','uncdn_highpt'])


def maketes(tes):
  """Interpolate."""
  # f = TFormula('f',sf)
  # for x in [10,34,35,(170+34)/2,100,169.9,170,171,200,2000]: x, f.Eval(x)
  #return f"x<34?{low}: x<170?{low}+({high}-{low})/(170.-34.)*(x-34): {high}"
  gradup = (tes.uncup_highpt-tes.uncup_lowpt)/(170.-34.)
  graddn = (tes.uncdn_highpt-tes.uncdn_lowpt)/(170.-34.)
  offsup = tes.nom+tes.uncup_lowpt-34.*gradup
  offsdn = tes.nom-tes.uncdn_lowpt+34.*graddn
  data   = [ # key:syst
    { 'key': 'nom',  'value': tes.nom }, # central value
    { 'key': 'up', 'value': { # down
        'nodetype': 'binning',
        'input': "pt",
        'edges': [0.,34.,170.,1000.],
        'flow': "clamp",
        'content': [
          tes.nom+tes.uncup_lowpt,
          { 'nodetype': 'formula', # down (pt-dependent)
            'expression': "%.6g+%.6g*x"%(offsup,gradup),
            'parser': "TFormula",
            'variables': ["pt"],
          },
          tes.nom+tes.uncup_highpt,
        ],
      },
    },
    { 'key': 'down', 'value': { # down
        'nodetype': 'binning',
        'input': "pt",
        'edges': [0.,34.,170.,1000.],
        'flow': "clamp",
        'content': [
          tes.nom-tes.uncdn_highpt,
          { 'nodetype': 'formula', # down (pt-dependent)
            'expression': "%.6g-%.6g*x"%(offsdn,graddn),
            'parser': "TFormula",
            'variables': ["pt"],
          },
          tes.nom-tes.uncdn_highpt,
        ],
      },
    },
  ]
  return data
  

def test_tes(corrs):
  """TES"""
  header("Tau energy scale")
  fname   = "data/tau/tau_tes.json"
  ptbins  = [0.,34.,170.]
  etabins = [0.,1.5,2.5]
  dms     = [
    0, 1, 10, 11
  ]
  fesdms  = [0,1] # for FES only DM0 and 1
  tes     = {dm: TES(1.0,0.1,0.2,0.1,0.2) for dm in dms} # nom uplow uphigh downlow downhigh
  fes     = {dm: [(1.0,1.2,0.8)]*(len(etabins)-1) for dm in fesdms} # nom uplow uphigh downlow downhigh
  
  # REAL TAU (genmatch==5)
  tesdata = { # category:dm -> category:syst
    'nodetype': 'category', # category:dm
    'input': "dm",
    'default': 1.0, # default TES if unrecognized DM
    'content': [ # key:dm
      { 'key': dm,
        'value': {
          'nodetype': 'category', # category:syst
          'input': "syst",
          'content': maketes(tes[dm])
        } # category:syst
      } for dm in dms
    ] # key:dm
  } # category:dm
  
  # E -> TAU FAKE (genmatch==1,3)
  fesdata = { # category:dm -> transform:eta -> binning:eta -> category:syst
    'nodetype': 'category', # category:dm
    'input': "dm",
    'default': 1.0, # default FES
    'content': [ # key:dm
      { 'key': dm,
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
            'edges': etabins,
            'flow': "clamp",
            'content': [
              { 'nodetype': 'category', # category:syst
                'input': "syst",
                'content': [
                  { 'key': 'nom',  'value': f[0] },
                  { 'key': 'up',   'value': f[1] },
                  { 'key': 'down', 'value': f[2] },
                ]
              } for f in fes[dm] # category:syst
            ]
          } # binning:eta
        } # transform:eta
      } for dm in fesdms
    ] # key:dm
  } # category:dm
  
  # MU -> TAU FAKE (genmatch==2,4)
  mesdata = {
    'nodetype': 'category', # category:syst
    'input': "syst",
    'default': 1.0,
    'content': [
      { 'key': 'up',   'value': 1.01 },
      { 'key': 'down', 'value': 0.99 },
    ]
  } # category:syst
  
  # CORRECTION OBJECT
  corr = Correction.parse_obj({
    'version': 0,
    'name': "test_tau_energy_scale",
    'description': "tau energy scale center around 1, to be applied to pt, mass and energy of the reconstructed tau_h in simulated data",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "tau pt"},
      {'name': "eta",      'type': "real",   'description': "tau eta"},
      {'name': "dm",       'type': "int",    'description': "tau decay mode (0, 1, 10, or 11)"},
      {'name': "genmatch", 'type': "int",    'description': "genmatch (0 or 6: no match, jet, 1 or 3: electron, 2 or 4: muon, 5: real tau"},
      {'name': "syst",     'type': "string", 'description': "systematic 'nom', 'up', 'down'"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:genmatch -> key:genmatch
      'nodetype': 'category', # category:genmatch
      'input': "genmatch",
      'default': 1.0, # default TES if unrecognized genmatch
      'content': [
        { 'key': 1, 'value': fesdata }, # e  -> tau_h fake
        { 'key': 2, 'value': mesdata }, # mu -> tau_h fake
        { 'key': 3, 'value': fesdata }, # e  -> tau_h fake
        { 'key': 4, 'value': mesdata }, # mu -> tau_h fake
        { 'key': 5, 'value': tesdata }, # real tau_h
      ]
    } # category:genmatch
  })
  
  # WRITE
  print(corr)
  #print(corr.data.content)
  print(f">>> Writing {fname}...")
  with open(fname,'w') as fout:
    fout.write(corr.json(exclude_unset=True,indent=2))
  corrs.append(corr)
  

def evaluate(corrs):
  header("Evaluate")
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  ptbins  = [10.,20.,30.,100.,170.,500.,2000.]
  etabins = [-2.0,-1.0,0.0,1.1,2.0,2.5,2.6]
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    #print(corr.inputs)
    for gm in [0,1,2,3,4,5,6]:
      xbins = ptbins if gm==5 else etabins
      ttype = "real tau_h" if gm==5 else "e -> tau_h" if gm in [1,3] else "mu -> tau_h" if gm in [2,4] else "j -> tau_h"
      print(f">>>\n>>> genmatch={gm}: {ttype}")
      print(">>> %5s"%("dm")+" ".join("  %-15.1f"%(x) for x in xbins))
      for dm in [0,1,2,10,11]:
        row   = ">>> %5d"%(dm)
        for x in xbins:
          pt, eta = (x,1.5) if gm==5 else (20.,x)
          sfnom = 0.0
          for syst in ['nom','up','down']:
            #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
            try:
              sf = corr.evaluate(pt,eta,dm,gm,syst)
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
  test_tes(corrs)
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
