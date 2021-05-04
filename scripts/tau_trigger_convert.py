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
import numpy

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
  
def merge_pt_bins(edges, values, errors):

  tmp_values = []
  tmp_errors = []

  bin_nb = 0
  n_merges = 0
  original_val = 0
  for val, err in zip(values, errors):
    if bin_nb > 0 and val == tmp_values[-1] and err == tmp_errors[-1]:
      edges.pop(bin_nb)
    elif bin_nb > 0 and abs((val-original_val)/original_val) < 0.005 and n_merges < 4:
      tmp_values[-1] = (tmp_values[-1] + val)/2
      tmp_errors[-1] = max(err, tmp_errors[-1])
      edges.pop(bin_nb)
      n_merges += 1
    else:
      tmp_values.append(val)
      tmp_errors.append(err)
      bin_nb += 1
      n_merges = 0
      original_val = val
  
  return edges, tmp_values, tmp_errors

def build_pts(in_file, hist_name):

  f = uproot.open(in_file)
  hist = f[hist_name]
  edges = [x for x in hist.to_numpy()[1]]

  edges, tmp_values, tmp_errors = merge_pt_bins(edges, hist.values(), hist.errors())

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

# Define parameters to fill
years = [2016, 2017, 2018]
wps     = [
  'VVVLoose', 'VVLoose', 'VLoose',
  'Loose', 'Medium', 'Tight',
  'VTight', 'VVTight'
]
# wps = ['Loose']
corrtypes = ['sf', 'eff_mc', 'eff_data']

# Define DM's
types_with_mergeddm = ['ditauvbf']

dms_nonmerged = [-1, 0, 1, 10, 11]
dms_merged = [-1, 0, 1, 10]

dm_dict_nonmerged = {
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

trigtypes = {
    2016 : ['ditau', 'etau', 'mutau'],
    2017 : ['ditau', 'etau', 'mutau', 'ditauvbf'],
    2018 : ['ditau', 'etau', 'mutau', 'ditauvbf'],
}

corrtype_dict = {
  'sf' : 'sf',
  'eff_mc' : 'mc',
  'eff_data' : 'data',
}

in_file_name = lambda year : 'data/tau/'+str(year)+'_tauTriggerEff_DeepTau2017v2p1.root'
in_hist_name = lambda corrtype, typ, wp, dm_str : '_'.join([corrtype,typ,wp,dm_str,'fitted'])

def build_dms(trigtype, wp, year, corrtype):
  print('Filling {0} {1} trigger for {2} WP'.format(year, trigtype, wp))

  if not trigtype in types_with_mergeddm:
    return Category.parse_obj(
      {
        'nodetype': 'category', # category:wp
        'input': "dm",
        'default': -1, # default DM if unrecognized category
        'content': [
          { 'key': dm,
            'value': 
              build_pts(in_file_name(year), in_hist_name(corrtype_dict[corrtype],trigtype,wp,dm_dict_nonmerged[dm]))
          } for dm in dms_nonmerged
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
                build_pts(in_file_name(year), in_hist_name(corrtype_dict[corrtype],trigtype,wp,dm_dict_merged[dm]))
            } for dm in dms_merged
          ]
        }
      } # category
    )

def convert_trigger(corrs, year):
  """Tau trigger SF, pT- and dm dependent."""
  header("Tau trigger SF, pT- and dm dependent")
  fname   = "data/tau/tau_trigger"+str(year)+".json"
  corr    = Correction.parse_obj({
    'version': 0,
    'name':    "test_DeepTau2017v2p1VSjet",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "tau pt"},
      {'name': "trigtype",       'type': "string",    'description': "Type of trigger: 'ditau', 'etau', 'mutau'"},
      {'name': "corrtype",       'type': "string",    'description': "Type of information: 'eff_data', 'eff_mc', 'sf'"},
      {'name': "wp",       'type': "string", 'description': "DeepTauVSjet WP: VVVLoose-VVTight"},
      {'name': "syst",     'type': "string", 'description': "systematic 'nom', 'up', 'down'"},
      {'name': "dm",       'type': "int",    'description': "tau decay mode (0, 1, 10, or 11)"},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:year -> category:trigtype -> category:wp -> category dm -> binning:pt -> category:syst
      'nodetype': 'category', # category:genmatch
      'input': "trigtype",
      'content': [
        { 'key': trigtype,
          'value': {
            'nodetype': 'category', # category:genmatch
            'input': "corrtype",
            'content' : [
              { 'key' : corrtype,
                'value' : {
                  'nodetype': 'category', # category:dm
                  'input': "wp",
                  'content': [
                    { 'key': wp,
                      'value' : build_dms(trigtype, wp, year, corrtype)
                    } for wp in wps
                  ]
                }
              } for corrtype in corrtypes
            ]  
          } # category:wp
        } for trigtype in trigtypes[year]
      ]
    } #category:trigtype
  })
  # print(corr)
  # print(corr.data.content)
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
    for wp in wps:
      print(f">>>\n>>> WP={wp}")
      for dm in dms_nonmerged:
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

def makeRootFiles(corrs, year):
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  out_file = ROOT.TFile('data/tau/correctionHistogramsRebinned_'+str(year)+'.root', 'recreate')
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    for corrtype in corrtypes:
      for wp in wps:
        print(f">>>\n>>> WP={wp}")
        for dm in dms_nonmerged:
          print(f">>>\n>>> DM={dm}")
          print(">>> %8s"%("trigger type"))
          for tt in trigtypes[year]:
            print('Building histogram')
            f = uproot.open(in_file_name(year))
            if tt in types_with_mergeddm:
              hist = f[in_hist_name(corrtype_dict[corrtype], tt, wp, dm_dict_merged[dm])]
            else:
              hist = f[in_hist_name(corrtype_dict[corrtype], tt, wp, dm_dict_nonmerged[dm])]
            edges = [x for x in hist.to_numpy()[1]]
            ptbin_edges, tmp_values, tmp_errors = merge_pt_bins(edges, hist.values(), hist.errors())

            hist = ROOT.TH1D('-'.join([corrtype_dict[corrtype], wp, str(dm), tt]), '-'.join([corrtype_dict[corrtype], wp, str(dm), tt]), len(ptbin_edges)-1, numpy.array(ptbin_edges))
            for pt_bin in range(1, len(ptbin_edges)):
              pt_bin_center = ptbin_edges[pt_bin-1]+ (ptbin_edges[pt_bin] - ptbin_edges[pt_bin-1])/2.
              try:
                hist.SetBinContent(pt_bin, corr.evaluate(pt_bin_center, tt, corrtype,wp,'nominal',dm))
                hist.SetBinError(pt_bin, corr.evaluate(pt_bin_center, tt, corrtype, wp,'up',dm)-corr.evaluate(pt_bin_center, tt, corrtype,wp,'nominal',dm) )
              except:
                print("Errors for {0} trigger with {1} wp and dm={2} for pt={3}GeV".format(tt, wp, str(dm), str(pt_bin_center)))
            hist.Write()
  out_file.Close()
  print(">>>")

def compareSFs(corrs, year):
  from TauAnalysisTools.TauTriggerSFs.SFProvider import SFProvider
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  ptbins = numpy.arange(20, 1000, 0.1)
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    for wp in wps:
      print(f">>>\n>>> WP={wp}")
      print(">>> %8s"%("trigger type"))
      for tt in trigtypes[year]:
        dms = [0, 1, 10, 11]
        for dm in dms:
          print(f">>>\n>>> DM={dm}")
          old_sfs = SFProvider(in_file_name(year), tt, wp)
          for pt in ptbins:
            if abs((old_sfs.getSF(pt, dm, 0) - corr.evaluate(pt, tt,'sf', wp,'nominal',dm))/old_sfs.getSF(pt, dm, 0)) > 0.01:
              print("Large difference in SF ({0}) for {1}, {2}, {3}, {4}, {5}".format(str((old_sfs.getSF(pt, dm, 0) - corr.evaluate(pt, tt,'sf', wp,'nominal',dm))/old_sfs.getSF(pt, dm, 0)), year, tt, wp, str(dm), str(pt)))
              print("Old: {0} New: {1}".format(old_sfs.getSF(pt, dm, 0), corr.evaluate(pt,tt,'sf',wp,'nominal',dm)))
            if abs((old_sfs.getEfficiencyMC(pt, dm, 0) - corr.evaluate(pt, tt,'eff_mc', wp,'nominal',dm))/old_sfs.getEfficiencyMC(pt, dm, 0)) > 0.01:
              print("Large difference in MC EFF ({0}) for {1}, {2}, {3}, {4}, {5}".format(str((old_sfs.getEfficiencyMC(pt, dm, 0) - corr.evaluate(pt, tt,'eff_mc',wp,'nominal',dm))/old_sfs.getEfficiencyMC(pt, dm, 0)), year, tt, wp, str(dm), str(pt)))
              print("Old: {0} New: {1}".format(old_sfs.getEfficiencyMC(pt, dm, 0), corr.evaluate(pt,tt,'eff_mc',wp,'nominal',dm)))
            if abs((old_sfs.getEfficiencyData(pt, dm, 0) - corr.evaluate(pt, tt,'eff_data', wp,'nominal',dm))/old_sfs.getEfficiencyData(pt, dm, 0)) > 0.01:
              print("Large difference in Data EFF ({0}) for {1}, {2}, {3}, {4}, {5}".format(str((old_sfs.getEfficiencyData(pt, dm, 0) - corr.evaluate(pt, tt,'eff_data',wp,'nominal',dm))/old_sfs.getEfficiencyData(pt, dm, 0)), year, tt, wp, str(dm), str(pt)))
              print("Old: {0} New: {1}".format(old_sfs.getEfficiencyData(pt, dm, 0), corr.evaluate(pt,tt,'eff_data',wp,'nominal',dm)))
            # if abs((old_sfs.getSF(pt, dm, 1) - corr.evaluate(pt, year, tt,wp,'up',dm))/old_sfs.getSF(pt, dm, 1)) > 0.01:
            #   print("Large difference in SF up unc ({0}) for {1}, {2}, {3}, {4}, {5}".format(str((old_sfs.getSF(pt, dm, 1) - corr.evaluate(pt, year, tt,wp,'up',dm))/old_sfs.getSF(pt, dm, 1)), year, tt, wp, str(dm), str(pt)))
            #   print("Old: {0} New: {1}".format(old_sfs.getSF(pt, dm, 1), corr.evaluate(pt, year, tt,wp,'up',dm)))
            # if abs((old_sfs.getSF(pt, dm, -1) - corr.evaluate(pt, year, tt,wp,'down',dm))/old_sfs.getSF(pt, dm, -1)) > 0.01:
            #   print("Large difference in SF down unc ({0}) for {1}, {2}, {3}, {4}, {5}".format(str((old_sfs.getSF(pt, dm, -1) - corr.evaluate(pt, year, tt,wp,'down',dm))/old_sfs.getSF(pt, dm, -1)), year, tt, wp, str(dm), str(pt)))
            #   print("Old: {0} New: {1}".format(old_sfs.getSF(pt, dm, -1), corr.evaluate(pt, year, tt,wp,'down',dm)))


  print(">>>")

def main():
  corrs = [ ] # list of corrections
  # test_trigger(corrs)
  # evaluate(corrs)
  for year in [2016, 2017, 2018]:
    convert_trigger(corrs, year)
    makeRootFiles(corrs, year)
    compareSFs(corrs, year)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
