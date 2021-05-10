#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with format of TauPOG SFs.
# Instructions:
#  ./scripts/tau_tid.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html#Tau
import sys; sys.path.append('scripts')
from utils import *


def maketid(sfs,pt,syst='nom'):
  """Interpolate for second to last bin."""
  # f = TFormula('f',sf)
  # for x in [10,20,29,30,31,35,45,100,200,499,500,501,750,999,1000,1001,1500,2000]: x, f.Eval(x)
  # "x<20?0: x<25?1.00: x<30?1.01: x<35?1.02: x<40?1.03: 1.04"
  # "x<20?0: x<25?1.10: x<30?1.11: x<35?1.12: x<40?1.13: x<500?1.14: x<1000?1.04+0.2*x/500.: 1.44"
  # "x<20?0: x<25?0.90: x<30?0.91: x<35?0.92: x<40?0.93: x<500?0.94: x<1000?1.04-0.2*x/500.: 0.64"
  #print(sfs,pt,syst)
  if syst=='nom':
    sf = sfs[0]
  else:
    sfnom, sfup, sfdown = sfs
    if pt<500: # pt < 500
      sf = sfnom-sfdown if syst=='down' else sfnom+sfup
    elif 500<=pt<1000: # 500 < pt < 1000
      sf = "%.6g-%.6g*x"%(sfnom,sfdown/500.) if syst=='down' else "%.6g+%.6g*x"%(sfnom,sfup/500.)
      sf = { # linearly inflate uncertainty x2
        'nodetype': 'formula', # pT-dependent
        'expression': sf,
        'parser': "TFormula",
        'variables': ["pt"],
      }
    else: # pt > 1000
      sf = sfnom-2*sfdown if syst=='down' else sfnom+2*sfup # inflate uncertainty x2
  return sf
  

def maketiddata_pt(sfs,ptbins,wps):
  """Construct tau energy scale data block."""
  tiddata = schema.Category.parse_obj({ # category:genmatch -> category:wp -> binning:eta -> category:syst
    'nodetype': 'category', # category:genmatch
    'input': "genmatch",
    #'default': 1.0, # no default: throw error if unrecognized genmatch
    'content': [
      { 'key': 0, 'value': 1.0 }, # j  -> tau_h fake
      { 'key': 1, 'value': 1.0 }, # e  -> tau_h fake
      { 'key': 2, 'value': 1.0 }, # mu -> tau_h fake
      { 'key': 3, 'value': 1.0 }, # e  -> tau_h fake
      { 'key': 4, 'value': 1.0 }, # mu -> tau_h fake
      { 'key': 5,  # real tau_h
        'value': {
          'nodetype': 'category', # category:wp
          'input': "wp",
          #'default': 1.0, # no default: throw error if unrecognized WP
          'content': [ # key:wp
            { 'key': wp,
              'value': {
                'nodetype': 'binning', # binning:pt
                'input': "pt",
                'edges': ptbins,
                'flow': "clamp",
                'content': [ # bin:pt
                  { 'nodetype': 'category', # syst
                    'input': "syst",
                    'content': [
                      { 'key': 'nom',  'value': maketid(sf,pt,'nom')  },
                      { 'key': 'up',   'value': maketid(sf,pt,'up')   },
                      { 'key': 'down', 'value': maketid(sf,pt,'down') },
                    ]
                  } for pt, sf in zip(ptbins,sfs[wp]) # loop over pT bins
                ] # bin:pt
              } # binning:pt
            } for wp in wps
          ] # key:wp
        } # category:wp
      },
      { 'key': 6, 'value': 1.0 }, # j  -> tau_h fake
    ]
  }) # category:genmatch
  return tiddata
  

def maketiddata_dm(sfs,dms,wps):
  """Construct tau energy scale data block."""
  tiddata = schema.Category.parse_obj({ # category:genmatch -> category:wp -> category:dm -> category:syst
    'nodetype': 'category', # category:genmatch
    'input': "genmatch",
    #'default': 1.0, # no default: throw error if unrecognized genmatch
    'content': [
      { 'key': 1, 'value': 1.0 }, # e  -> tau_h fake
      { 'key': 2, 'value': 1.0 }, # mu -> tau_h fake
      { 'key': 3, 'value': 1.0 }, # e  -> tau_h fake
      { 'key': 4, 'value': 1.0 }, # mu -> tau_h fake
      { 'key': 5,  # real tau_h
        'value': {
          'nodetype': 'category', # category:wp
          'input': "wp",
          #'default': 1.0, # no default: throw error if unrecognized WP
          'content': [ # key:wp
            { 'key': wp,
              'value': {
                'nodetype': 'category', # category:dm
                'input': "dm",
                #'default': 1.0, # no default: throw error if unsupported DM
                'content': [ # key:dm
                  { 'key': dm,
                    'value': {
                      'nodetype': 'category', # syst
                      'input': "syst",
                      'content': [
                        { 'key': 'nom',  'value': sfs[wp][dm][0] },
                        { 'key': 'up',   'value': sfs[wp][dm][1] },
                        { 'key': 'down', 'value': sfs[wp][dm][2] },
                      ]
                    }
                  } for dm in dms
                ] # key:dm
              } # category:dm
            } for wp in wps
          ] # key:wp
        } # category:wp
      },
      { 'key': 6, 'value': 1.0 }, # j  -> tau_h fake
      { 'key': 0, 'value': 1.0 }, # j  -> tau_h fake
    ]
  }) # category:genmatch
  return tiddata
  

def makecorr_tid(ptsfs=None,dmsfs=None,**kwargs):
  """Tau ID SF, pT-dependent."""
  verb    = kwargs.get('verb',0)
  tag     = kwargs.get('tag',"") # output tag for JSON file
  outdir  = kwargs.get('outdir',"data/tau") # output directory for JSON file
  dms     = [0,1,2,10,11]
  ptbins  = kwargs.get('bins',[20.,25.,30.,35.,40.,500.,1000.,2000.])
  if ptsfs and dmsfs:
    id    = kwargs.get('id',   "unkown")
    era   = kwargs.get('era',  "unkown")
    name  = kwargs.get('name', f"tau_sf_pt-dm_{id}_{era}")
    fname = kwargs.get('fname',f"{outdir}/{name}{tag}.json")
    info  = kwargs.get('info', f"{id} SFs in {era}")
    ptwps = list(ptsfs.keys())
    dmwps = list(dmsfs.keys())
    print(dmsfs,dmwps)
    dms   = list(dmsfs[dmwps[0]].keys()) # get list of DMs from first WP
  else: # test format with dummy values
    id    = kwargs.get('id',  "DeepTau2017v2p1VSjet")
    header(f"Dummy {id} SFs for test")
    name  = kwargs.get('name', f"test_{id}_pt-dm")
    fname = kwargs.get('fname',f"{outdir}/test_tau_pt-dm{tag}.json")
    info  = kwargs.get('info', f"{id} SFs")
    ptwps = [
      #'VVVLoose', 'VVLoose', 'VLoose',
      'Loose', 'Medium', 'Tight',
      #'VTight', 'VVTight'
    ]
    dmwps = ptwps
    ptsfs = {wp: [(1.,0.2,0.2) for i in range(len(ptbins)-1)] for wp in wps}
    dmsfs = {wp: {dm: (1.,0.2,0.2) for dm in dms} for wp in wps}
  assert all(len(ptsfs[w])==len(ptbins)-1 for w in ptsfs), f"Number of SFs ({sfs}) does not match ({len(ptbins)-1})!"
  assert ptbins[-3]==500.,  f"Third-to-last bin ({ptbins[-3]}) should be 500!"
  assert ptbins[-2]==1000., f"Second-to-last bin ({ptbins[-2]}) should be 1000!"
  assert ptbins[-1]>1000.,  f"Last bin ({ptbins[-1]}) should be larger than 1000!"
  ptwps.sort(key=wp_sortkey)
  dmwps.sort(key=wp_sortkey)
  dms.sort()
  wps = ptwps if len(ptwps)>=len(dmwps) else dmwps
  corr = schema.Correction.parse_obj({
    'version': 0,
    'name': name,
    'description': f"{id} SFs: By default, use the pT-dependent SFs with the 'pt' flag. "+\
                   "For analyses with the ditau triggers with offline pT > 40 GeV, "+\
                   "use the DM-dependent SFs with flag 'dm'.",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "Reconstructed tau pT"},
      {'name': "dm",       'type': "int",    'description': getdminfo(dms)},
      {'name': "genmatch", 'type': "int",    'description': getgminfo()},
      {'name': "wp",       'type': "string", 'description': getwpinfo(id,wps)},
      {'name': "syst",     'type': "string", 'description': "Systematic 'nom', 'up', 'down'"},
      {'name': "flag",     'type': "string", 'description': "Flag: 'pt' = pT-dependent SFs, 'dm' = DM-dependent SFs (pT > 40 GeV)"},
    ],
    'output': {'name': "sf", 'type': "real", 'description': "{id} scale factor"},
    'data': schema.Category.parse_obj({ # category:genmatch -> category:wp -> category:dm -> category:syst
      'nodetype': 'category', # category:genmatch
      'input': "flag",
      #'default': 1.0, # no default: throw error if unrecognized genmatch
      'content': [
        { 'key': 'pt', 'value': maketiddata_pt(ptsfs,ptbins,ptwps) },
        { 'key': 'dm', 'value': maketiddata_dm(dmsfs,dms,dmwps) },
      ],
    })
  })
  if verb>=2:
    print(JSONEncoder.dumps(corr))
  elif verb>=1:
    print(corr)
  if fname:
    print(f">>> Writing {fname}...")
    JSONEncoder.write(corr,fname)
  return corr
  

def makecorr_tid_pt(sfs=None,**kwargs):
  """Tau ID SF, pT-dependent."""
  verb    = kwargs.get('verb',0)
  tag     = kwargs.get('tag',"") # output tag for JSON file
  outdir  = kwargs.get('outdir',"data/tau") # output directory for JSON file
  ptbins  = kwargs.get('bins',[20.,25.,30.,35.,40.,500.,1000.,2000.])
  if sfs:
    id    = kwargs.get('id',   "unkown")
    era   = kwargs.get('era',  "unkown")
    name  = kwargs.get('name', f"tau_sf_pt_{id}_{era}")
    fname = kwargs.get('fname',f"{outdir}/{name}{tag}.json")
    info  = kwargs.get('info', f"pT-dependent SFs for {id} in {era}")
    wps   = list(sfs.keys())
  else: # test format with dummy values
    id    = kwargs.get('id',  "DeepTau2017v2p1VSjet")
    header(f"Dummy pT-dependent {id} SFs for test")
    name  = kwargs.get('name', f"test_{id}_pt")
    fname = kwargs.get('fname',f"{outdir}/test_tau_pt{tag}.json")
    info  = kwargs.get('info', f"pT-dependent SFs for {id}")
    wps   = [
      #'VVVLoose', 'VVLoose', 'VLoose',
      'Loose', 'Medium', 'Tight',
      #'VTight', 'VVTight'
    ]
    sfs   = {wp: [(1.,0.2,0.2) for i in range(len(ptbins)-1)] for wp in wps}
  assert all(len(sfs[w])==len(ptbins)-1 for w in sfs), f"Number of SFs ({sfs}) does not match ({len(ptbins)-1})!"
  assert ptbins[-3]==500., f"Third-to-last bin ({ptbins[-3]}) should be 500!"
  assert ptbins[-2]==1000., f"Second-to-last bin ({ptbins[-2]}) should be 1000!"
  assert ptbins[-1]>1000., f"Last bin ({ptbins[-1]}) should be larger than 1000!"
  wps.sort(key=wp_sortkey)
  corr    = schema.Correction.parse_obj({
    'version': 0,
    'name': name,
    'description': "pT-dependent SFs for DeepTau2017v2p1VSjet",
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "Reconstructed tau pT"},
      {'name': "genmatch", 'type': "int",    'description': getgminfo()},
      {'name': "wp",       'type': "string", 'description': getwpinfo(id,wps)},
      {'name': "syst",     'type': "string", 'description': "Systematic 'nom', 'up', 'down'"},
    ],
    'output': {'name': "sf", 'type': "real", 'description': "pT-dependent {id} scale factor"},
    'data': maketiddata_pt(sfs,ptbins,wps)
  })
  if verb>=2:
    print(JSONEncoder.dumps(corr))
  elif verb>=1:
    print(corr)
  if fname:
    print(f">>> Writing {fname}...")
    JSONEncoder.write(corr,fname)
  return corr
  

def makecorr_tid_dm(sfs=None,**kwargs):
  """Tau ID SF, DM-dependent."""
  verb    = kwargs.get('verb',0)
  tag     = kwargs.get('tag',"") # output tag for JSON file
  outdir  = kwargs.get('outdir',"data/tau") # output directory for JSON file
  if sfs:
    id    = kwargs.get('id',   "unkown")
    era   = kwargs.get('era',  "unkown")
    name  = kwargs.get('name', f"tau_sf_dm_{id}_{era}")
    fname = kwargs.get('fname',f"{outdir}/{name}{tag}.json")
    info  = kwargs.get('info', f"DM-dependent SFs for {id} in {era} with tau_h pT > 40 GeV")
    wps   = list(sfs.keys())
    dms   = list(sfs[wps[0]].keys()) # get list of DMs from first WP
  else: # test format with dummy values
    id    = kwargs.get('id',  "DeepTau2017v2p1VSjet")
    header(f"Dummy DM-dependent {id} SFs for test")
    name  = kwargs.get('name', f"test_{id}_dm")
    fname = kwargs.get('fname',f"{outdir}/test_tau_dm{tag}.json")
    info  = kwargs.get('info', f"DM-dependent SFs for {id} with tau_h pT > 40 GeV")
    wps   = [
      #'VVVLoose', 'VVLoose', 'VLoose',
      'Loose', 'Medium', 'Tight',
      #'VTight', 'VVTight'
    ]
    dms   = [0,1,2,10,11]
    sfs   = {wp: {dm: (1.,0.2,0.2) for dm in dms} for wp in wps}
  wps.sort(key=wp_sortkey)
  dms.sort()
  corr = schema.Correction.parse_obj({
    'version': 0,
    'name': name,
    'description': info,
    'inputs': [
      #{'name': "pt",       'type': "real",   'description': "Reconstructed tau pT"},
      {'name': "dm",       'type': "int",    'description': getdminfo(dms)},
      {'name': "genmatch", 'type': "int",    'description': getgminfo()},
      {'name': "wp",       'type': "string", 'description': getwpinfo(id,wps)},
      {'name': "syst",     'type': "string", 'description': getsystinfo()},
    ],
    'output': {'name': "sf", 'type': "real", 'description': "DM-dependent {id} scale factor"},
    'data': maketiddata_dm(sfs,dms,wps)
  })
  if verb>=2:
    print(JSONEncoder.dumps(corr))
  elif verb>=1:
    print(corr)
  if fname:
    print(f">>> Writing {fname}...")
    JSONEncoder.write(corr,fname)
  return corr
  

def evaluate(corrs):
  header("Evaluate")
  cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  dms  = [-1,0,1,2,5,10,11]
  gms  = [0,1,2,3,4,5,6,7]
  pts  = [10.,21.,26.,31.,36.,41.,501.,750.,999.,2000.]
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    wps = ['Medium','Tight']
    if 'dm' in name:
      xbins = dms
      head  = ">>> %8s"%("genmatch")+" ".join("  %-15d"%(d) for d in dms)
    else:
      xbins = pts
      head  = ">>> %8s"%("genmatch")+" ".join("  %-15.1f"%(p) for p in pts)
    for wp in wps:
      print(f">>>\n>>> WP={wp}")
      print(head)
      for gm in gms:
        row = ">>> %8d"%(gm)
        for x in xbins:
          sfnom = 0.0
          for syst in ['nom','up','down']:
            #print(">>>   gm=%d, eta=%4.1f, syst=%r sf=%s"%(gm,eta,syst,eval(corr,eta,gm,wp,syst)))
            try:
              sf = corr.evaluate(x,gm,wp,syst)
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
  corr1 = makecorr_tid_pt()
  corr2 = makecorr_tid_dm()
  corrs = [corr1,corr2]
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
