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
import uproot
import os, ROOT

from correctionlib.schemav2 import (
    VERSION,
    Binning,
    Category,
    Correction,
    CorrectionSet,
    Formula,
)

#
# Different test functions taken from data/conversion and adapted
#
def build_syst(val, err):
    return Category.parse_obj(
        {
            "nodetype": "category",
            "input": "syst",
            "content": [
                {"key": "nominal", "value": val},
                {"key": "up", "value": val+err},
                {"key": "down", "value": val-err},
            ],
        }
    )

#
# Check if valid ROOT file exists
#
def isValidRootFile(fname):
    if not os.path.exists(os.path.expandvars(fname)): return False
    if 'pnfs' in fname: fname = 'root://maite.iihe.ac.be'+ fname         #faster for pnfs files + avoids certain unstable problems I had with input/output errors
    f = ROOT.TFile.Open(fname)
    if not f: return False
    try:
        return not (f.IsZombie() or f.TestBit(ROOT.TFile.kRecovered) or f.GetListOfKeys().IsEmpty())
    finally:
        f.Close()

#
# Get object (e.g. hist) from file using key, and keep in memory after closing
#
def getObjFromFile(fname, hname):
    assert isValidRootFile(fname)

    if 'pnfs' in fname: fname = 'root://maite.iihe.ac.be'+ fname         #faster for pnfs file
    try:
        f = ROOT.TFile.Open(fname)
        f.cd()
        htmp = f.Get(hname)
        if not htmp: return None
        ROOT.gDirectory.cd('PyROOT:/')
        res = htmp.Clone()
        return res
    finally:
        f.Close()

#
# Temporarily load in uproot file and regular root file because I could not get the up and down values to work with uproot yet
#
def build_pts(in_file, hist_name):

    root_hist = getObjFromFile(in_file, hist_name)
    uproot_f = uproot.open(in_file)
    uproot_hist = uproot_f[hist_name]

    edges = [x for x in uproot_hist.numpy()[1]]
    content = []
    for ib, b in enumerate(uproot_hist.numpy()[0]):
        content.append(build_syst(b, root_hist.GetBinError(ib+1)))

    return Binning.parse_obj(
        {
            "nodetype": "binning",
            "input": "pt",
            "edges": edges,
            "content": content,
            "flow": "clamp",
        }
    )


in_file_name = 'data/tau/2018_tauTriggerEff_DeepTau2017v2p1.root'
dm_dict = {
  -1: 'dmall',
  0 : 'dm0',
  1 : 'dm1',
  10 : 'dm10',
  11 : 'dm11'
}
in_hist_name = lambda typ, wp, dm_str : '_'.join(['sf',typ,wp,dm_str,'fitted'])

def test_trigger(corrs):
  """Tau trigger SF, pT- and dm dependent."""
  header("Tau trigger SF, pT- and dm dependent")
  fname   = "data/tau/tau_trigger.json"
  dms     = [
    -1, 0, 1, 10, 11
    # -1
  ]
  wps     = [
    #'VVVLoose', 'VVLoose', 'VLoose',
    'Loose', 'Medium', 'Tight',
    #'VTight', 'VVTight'
  ]
  trigtypes = [
      # 'ditau'
      'ditau', 'etau', 'mutau'
  ]
  ptbins  = [20.,25.,30.,35.,40.,500.,1000.]
  nptbins = len(ptbins)-1
  sfs     = {wp: [(1.,0.2,0.2) for i in range(nptbins)] for wp in wps}
  corr    = Correction.parse_obj({
    'version': 0,
    'name':    "test_DeepTau2017v2p1VSjet",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "tau pt"},
      {'name': "trigtype",       'type': "string",    'description': "Type of trigger: 'ditau', 'etau', 'mutau'"},
      {'name': "wp",       'type': "string", 'description': "DeepTauVSjet WP: VVVLoose-VVTight"},
      {'name': "syst",     'type': "string", 'description': "systematic 'nom', 'up', 'down'"},
      {'name': "dm",       'type': "int",    'description': "tau decay mode (0, 1, 10, or 11)"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:trigtype -> category:wp -> binning:pt -> category:syst
      'nodetype': 'category', # category:genmatch
      'input': "trigtype",
      'content': [
        { 'key': trigtype,
          'value': {
            'nodetype': 'category', # category:dm
            'input': "dm",
            'default': -1, # default TES if unrecognized genmatch
            'content': [
              { 'key': dm,
                'value' : {
                  'nodetype': 'category', # category:wp
                  'input': "wp",
                  'content': [
                    { 'key': wp,
                      'value': 
                        build_pts(in_file_name, in_hist_name(trigtype,wp,dm_dict[dm]))
                    } for wp in wps
                  ]
                } # category:wp
              } for dm in dms
            ]  
          } # category:dm
        } for trigtype in trigtypes
      ]
    } # category:genmatch
  })
  print(corr)
  # print(corr.data.content)
  print(f">>> Writing {fname}...")
  with open(fname,'w') as fout:
    fout.write(corr.json(exclude_unset=True,indent=2))
  corrs.append(corr)
  
def test_trigger_wo_inputfile(corrs):
  """Tau trigger SF, pT- and dm dependent."""
  header("Tau trigger SF, pT- and dm dependent")
  fname   = "data/tau/tau_trigger.json"
  dms     = [
    -1, 0, 1, 10, 11
  ]
  wps     = [
    #'VVVLoose', 'VVLoose', 'VLoose',
    'Loose', 'Medium', 'Tight',
    #'VTight', 'VVTight'
  ]
  trigtypes = [
      'ditau', 'etau', 'mutau'
  ]
  ptbins  = [20.,25.,30.,35.,40.,500.,1000.]
  nptbins = len(ptbins)-1
  sfs     = {wp: [(1.,0.2,0.2) for i in range(nptbins)] for wp in wps}
  corr    = Correction.parse_obj({
    'version': 0,
    'name':    "test_DeepTau2017v2p1VSjet",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "tau pt"},
      {'name': "trigtype",       'type': "string",    'description': "Type of trigger: 'ditau', 'etau', 'mutau'"},
      {'name': "wp",       'type': "string", 'description': "DeepTauVSjet WP: VVVLoose-VVTight"},
      {'name': "syst",     'type': "string", 'description': "systematic 'nom', 'up', 'down'"},
      {'name': "dm",       'type': "int",    'description': "tau decay mode (0, 1, 10, or 11)"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:trigtype -> category:wp -> binning:pt -> category:syst
      'nodetype': 'category', # category:genmatch
      'input': "trigtype",
      'content': [
        { 'key': trigtype,
          'value': {
            'nodetype': 'category', # category:dm
            'input': "dm",
            'default': -1, # default TES if unrecognized genmatch
            'content': [
              { 'key': dm,
                'value' : {
                  'nodetype': 'category', # category:wp
                  'input': "wp",
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
              } for dm in dms
            ]  
          } # category:dm
        } for trigtype in trigtypes
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
    wps = ['Loose']
    for wp in wps:
      print(f">>>\n>>> WP={wp}")
      dms = [-1, 0, 1, 10, 11]
      for dm in dms:
        print(f">>>\n>>> DM={dm}")
        print(">>> %8s"%("trigger type")+" ".join("  %-15.1f"%(p) for p in ptbins))
        for tt in ['ditau', 'etau', 'mutau']:
          row = ">>> %s"%(tt)
          for pt in ptbins:
            sfnom = 0.0
            for syst in ['nom','up','down']:
              #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
              try:
                sf = corr.evaluate(pt,tt,wp,syst,20)
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
  test_trigger(corrs)
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
