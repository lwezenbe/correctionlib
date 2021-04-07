#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Author: Liam Wezenbeek (April 2021)
# Description: Script to play around with format of TauPOG trigger SFs. (based on tau_tid.py)
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
    Transform
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

def build_pts(in_file, hist_name):

    f = uproot.open(in_file)
    hist = f[hist_name]

    edges = [x for x in hist.to_numpy()[1]]
    tmp_values = []
    tmp_errors = []

    bin_nb = 0
    for val, err in zip(hist.values(), hist.errors()):
      if bin_nb > 0 and val == tmp_values[-1] and err == tmp_errors[-1]:
        edges.pop(bin_nb)
      else:
        tmp_values.append(val)
        tmp_errors.append(err)
        bin_nb += 1

    content = []
    for val, err in zip(tmp_values, tmp_errors):
        content.append(build_syst(val, err))

    return Binning.parse_obj(
        {
            "nodetype": "binning",
            "input": "pt",
            "edges": edges,
            "content": content,
            "flow": "clamp",
        }
    )


dms     = [
  -1, 0, 1, 10, 11
]
dms_merged     = [
  -1, 0, 1, 10
]

dm_dict = {
  -1: 'dmall',
  0 : 'dm0',
  1 : 'dm1',
  10 : 'dm10',
  11 : 'dm11'
}

dm_dict_merged = {
  -1: 'dmall',
  0 : 'dm0',
  1 : 'dm1',
  10 : 'dm1011',
  11 : 'dm1011'
}

in_file_name = lambda year : 'data/tau/'+str(year)+'_tauTriggerEff_DeepTau2017v2p1.root'
in_hist_name = lambda typ, wp, dm_str : '_'.join(['sf',typ,wp,dm_str,'fitted'])

def build_dms(trigtype, wp, year):
  print('Filling {0} {1} trigger for {2} WP'.format(year, trigtype, wp))

  if not 'ditauvbf' in trigtype:
    return Category.parse_obj(
      {
        'nodetype': 'category', # category:wp
        'input': "dm",
        'default': -1, # default DM if unrecognized category
        'content': [
          { 'key': dm,
            'value': 
              build_pts(in_file_name(year), in_hist_name(trigtype,wp,dm_dict[dm]))
          } for dm in dms
        ]
      } # category:dm
    )
  else:
    return Transform.parse_obj(
      {
        'nodetype': 'transform', # category:wp
        'input': "dm",
        'rule': {
          'nodetype': 'category', # category:dm
          'input': "dm",
          'content': [ # key:dm
            { 'key':  -1, 'value':  -1 },
            { 'key':  0, 'value':  0 },
            { 'key':  1, 'value':  1 },
            { 'key': 10, 'value': 10 },
            { 'key': 11, 'value': 10 }, # map 11 -> 10
          ] # key:dm
        }, # category:dm          
        'content': {
          'nodetype': 'category', # category:dm
          'input': "dm",
          'default': -1, # default DM if unrecognized genmatch
          'content' : [
            { 'key': dm,
              'value': 
                build_pts(in_file_name(year), in_hist_name(trigtype,wp,dm_dict_merged[dm]))
            } for dm in dms_merged
          ]
        }
      } # category
    )


def test_trigger(corrs):
  """Tau trigger SF, pT- and dm dependent."""
  header("Tau trigger SF, pT- and dm dependent")
  fname   = "data/tau/tau_trigger.json"
  years = [
    # 2016, 2017, 2018
    2017
  ]
  wps     = [
    # 'VVVLoose', 'VVLoose', 'VLoose',
    'Loose', 'Medium', 'Tight',
    # 'VTight', 'VVTight'
  ]
  trigtypes = {
      2016 : ['ditau', 'etau', 'mutau'],
      2017 : ['ditau', 'etau', 'mutau', 'ditauvbf'],
      2018 : ['ditau', 'etau', 'mutau', 'ditauvbf'],
  }
  corr    = Correction.parse_obj({
    'version': 0,
    'name':    "test_DeepTau2017v2p1VSjet",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "tau pt"},
      {'name': "year",       'type': "int",   'description': "year of datataking"},
      {'name': "trigtype",       'type': "string",    'description': "Type of trigger: 'ditau', 'etau', 'mutau'"},
      {'name': "wp",       'type': "string", 'description': "DeepTauVSjet WP: VVVLoose-VVTight"},
      {'name': "syst",     'type': "string", 'description': "systematic 'nom', 'up', 'down'"},
      {'name': "dm",       'type': "int",    'description': "tau decay mode (0, 1, 10, or 11)"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:year -> category:trigtype -> category:wp -> category dm -> binning:pt -> category:syst
      'nodetype' : 'category',
      'input' : 'year',
      'content' : [
        { 'key' : year,
          'value' : {
            'nodetype': 'category', # category:genmatch
            'input': "trigtype",
            'content': [
              { 'key': trigtype,
                'value': {
                  'nodetype': 'category', # category:dm
                  'input': "wp",
                  'content': [
                    { 'key': wp,
                      'value' : build_dms(trigtype, wp, year)
                    } for wp in wps
                  ]  
                } # category:wp
              } for trigtype in trigtypes[year]
            ]
          } #category:trigtype
        } for year in years
      ]
    } # category:year
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
    wps = ['Loose', 'Medium', 'tight']
    for wp in wps:
      print(f">>>\n>>> WP={wp}")
      dms = [-1, 0, 1, 10, 11]
      for dm in dms:
        print(f">>>\n>>> DM={dm}")
        print(">>> %8s"%("trigger type")+" ".join("  %-15.1f"%(p) for p in ptbins))
        for tt in ['ditau', 'etau', 'mutau', 'ditauvbf']:
          row = ">>> %s"%(tt)
          for pt in ptbins:
            sfnom = 0.0
            for syst in ['nominal','up','down']:
              #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
              try:
                sf = corr.evaluate(pt, 2017, tt,wp,syst,dm)
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
  
