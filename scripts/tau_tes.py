#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with format of TauPOG SFs.
# Instructions:
#  ./scripts/tau_tes.py
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc102X_doc.html#Tau
import sys; sys.path.append('scripts')
from utils import *
from collections import namedtuple
TES = namedtuple('TES',['nom','up_lowpt','dn_lowpt','up_highpt','dn_highpt']) # helper class


def maketes(tes):
  """Interpolate."""
  # f = TFormula('f',sf)
  # for x in [10,34,35,(170+34)/2,100,169.9,170,171,200,2000]: x, f.Eval(x)
  #return f"x<34?{low}: x<170?{low}+({high}-{low})/(170.-34.)*(x-34): {high}"
  gradup = (tes.up_highpt-tes.up_lowpt)/(170.-34.)
  graddn = (tes.dn_highpt-tes.dn_lowpt)/(170.-34.)
  offsup = tes.nom+tes.up_lowpt-34.*gradup
  offsdn = tes.nom-tes.dn_lowpt+34.*graddn
  data   = [ # key:syst
    { 'key': 'nom',  'value': tes.nom }, # central value
    { 'key': 'up', 'value': { # down
        'nodetype': 'binning',
        'input': "pt",
        'edges': [0.,34.,170.,1000.],
        'flow': "clamp",
        'content': [
          tes.nom+tes.up_lowpt,
          { 'nodetype': 'formula', # down (pt-dependent)
            'expression': "%.6g+%.6g*x"%(offsup,gradup),
            'parser': "TFormula",
            'variables': ["pt"],
          },
          tes.nom+tes.up_highpt,
        ],
      },
    },
    { 'key': 'down', 'value': { # down
        'nodetype': 'binning',
        'input': "pt",
        'edges': [0.,34.,170.,1000.],
        'flow': "clamp",
        'content': [
          tes.nom-tes.dn_highpt,
          { 'nodetype': 'formula', # down (pt-dependent)
            'expression': "%.6g-%.6g*x"%(offsdn,graddn),
            'parser': "TFormula",
            'variables': ["pt"],
          },
          tes.nom-tes.dn_highpt,
        ],
      },
    },
  ]
  return data
  

def makecorr_tes(tesvals=None,**kwargs):
  """TES"""
  verb    = kwargs.get('verb',0)
  outdir  = kwargs.get('outdir',"data/tau")
  info    = ", to be applied to reconstructed tau_h pt, mass and energy in simulated data"
  ptbins  = [0.,34.,170.]
  etabins = [0.,1.5,2.5]
  if tesvals:
    id      = kwargs.get('id',   "unkown")
    era     = kwargs.get('era',  "unkown")
    name    = kwargs.get('name', f"tau_sf_dm_{id}_{era}")
    fname   = kwargs.get('fname',f"{outdir}/{name}.json")
    info    = kwargs.get('info', f"DM-dependent tau energy scale for {id} in {era}"+info)
    ptbins  = kwargs.get('ptbins',ptbins)
    etabins = kwargs.get('etabins',etabins)
    dms     = list(tesvals['low'].keys())
    fesdms  = list(tesvals['ele'].keys())
    fesvals = tesvals['ele'] # dm -> (nom,up,down)
    tesvals = { # dm -> TES(nom,uplow,downlow,uphigh,downhigh)
      dm: TES(*tesvals['low'][dm],*tesvals['high'][dm][1:]) for dm in dms
    }
  else: # test format with dummy values
    id      = kwargs.get('id',  "DeepTau2017v2p1VSjet")
    header(f"Tau energy scale for {id}")
    name    = kwargs.get('name', f"test_{id}_dm")
    fname   = kwargs.get('fname',f"{outdir}/test_tau_tes.json")
    info    = kwargs.get('info', f"DM-dependent tau energy scale for {id}"+info)
    dms     = [0,1,2,10,11]
    fesdms  = [0,1,2] # for FES only DM0 and 1
    tesvals = {dm: TES(1.0,0.1,0.1,0.2,0.2) for dm in dms} # (nom,uplow,downlow,uphigh,downhigh)
    fesvals = {dm: [(1.0,1.2,0.8)]*(len(etabins)-1) for dm in fesdms} # (nom,up,down)
  dms.sort()
  fesdms.sort()
  
  # REAL TAU (genmatch==5)
  tesdata = { # category:dm -> category:syst
    'nodetype': 'category', # category:dm
    'input': "dm",
    #'default': 1.0, # no default: throw error if unsupported DM
    'content': [ # key:dm
      { 'key': dm,
        'value': {
          'nodetype': 'category', # category:syst
          'input': "syst",
          'content': maketes(tesvals[dm])
        } # category:syst
      } for dm in dms
    ] # key:dm
  } # category:dm
  
  # E -> TAU FAKE (genmatch==1,3)
  fesdata = { # category:dm -> transform:eta -> binning:eta -> category:syst
    'nodetype': 'category', # category:dm
    'input': "dm",
    #'default': 1.0, # no default: throw error if unsupported DM
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
                  { 'key': 'nom',  'value': fes[0] },
                  { 'key': 'up',   'value': fes[1] },
                  { 'key': 'down', 'value': fes[2] },
                ]
              } for fes in fesvals[dm] # category:syst
            ]
          } # binning:eta
        } # transform:eta
      } for dm in fesdms
    ]+[
      { 'key': dm, 'value': 1.0 } # default for supported DMs
      for dm in dms if dm not in fesdms
    ] # key:dm
  } # category:dm
  
  # MU -> TAU FAKE (genmatch==2,4)
  mesdata = {
    'nodetype': 'category', # category:syst
    'input': "syst",
    'content': [
      { 'key': 'nom',  'value': 1.00 },
      { 'key': 'up',   'value': 1.01 },
      { 'key': 'down', 'value': 0.99 },
    ]
  } # category:syst
  
  # CORRECTION OBJECT
  corr = Correction.parse_obj({
    'version': 0,
    'name': "test_tau_energy_scale",
    'description': info,
    'inputs': [
      {'name': "pt",       'type': "real",   'description': "Reconstructed tau pt"},
      {'name': "eta",      'type': "real",   'description': "Reconstructed tau eta"},
      {'name': "dm",       'type': "int",    'description': getdminfo(dms)},
      {'name': "genmatch", 'type': "int",    'description': getgminfo()},
      {'name': "syst",     'type': "string", 'description': getsystinfo()},
    ],
    'output': {'name': "weight", 'type': "real"},
    'data': { # category:genmatch -> key:genmatch
      'nodetype': 'category', # category:genmatch
      'input': "genmatch",
      #'default': 1.0, # no default: throw error if unrecognized genmatch
      'content': [
        { 'key': 1, 'value': fesdata }, # e  -> tau_h fake
        { 'key': 2, 'value': mesdata }, # mu -> tau_h fake
        { 'key': 3, 'value': fesdata }, # e  -> tau_h fake
        { 'key': 4, 'value': mesdata }, # mu -> tau_h fake
        { 'key': 5, 'value': tesdata }, # real tau_h
        { 'key': 6, 'value': 1.0 }, # j  -> tau_h fake
        { 'key': 0, 'value': 1.0 }, # j  -> tau_h fake
      ]
    } # category:genmatch
  })
  
  if verb>1:
    print(JSONEncoder.dumps(corr))
  elif verb>0:
    print(corr)
  if fname:
    print(f">>> Writing {fname}...")
    JSONEncoder.write(corr,fname)
  return corr
  

def evaluate(corrs):
  header("Evaluate")
  cset_py, cset = wrap(corrs) # wrap to create C++ object that can be evaluated
  ptbins  = [10.,20.,30.,100.,170.,500.,2000.]
  etabins = [-2.0,-1.0,0.0,1.1,2.0,2.5,3.0]
  gms     = [0,1,2,3,4,5,6,7]
  dms     = [0,1,2,5,10,11]
  for name in list(cset):
    corr = cset[name]
    print(f">>>\n>>> {name}: {corr.description}")
    #print(corr.inputs)
    for gm in gms:
      xbins = ptbins if gm==5 else etabins
      ttype = "real tau_h" if gm==5 else "e -> tau_h" if gm in [1,3] else\
              "mu -> tau_h" if gm in [2,4] else "j -> tau_h" if gm in [0,6] else "non-existent"
      print(f">>>\n>>> genmatch={gm}: {ttype}")
      print(">>> %5s"%("dm")+" ".join("  %-15.1f"%(x) for x in xbins))
      for dm in dms:
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
  corr1 = makecorr_tes(corrs)
  corrs = [corr1] # list of corrections
  evaluate(corrs)
  #write(corrs)
  #read(corrs)
  

if __name__ == '__main__':
  main()
  print()
  
