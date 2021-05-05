#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to compare old ROOT to new JSON SF tools for validation
# Instructions:
#   git clone https://github.com/cms-tau-pog/TauIDSFs TauIDSFs
#   scripts/tau_compare_tools.py
#   scripts/tau_compare_tools.py -I DeepTau2017v2p1VSjet -y 2018ReReco -g 1 2 5 6
#   scripts/tau_compare_tools.py -E DeepTau2017v2p1 -y 2018ReReco -d 0 1 10 11 -g 1 2 5 6
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/python/TauIDSFTool.py
import os, sys
sys.path.append('scripts')
sys.path.append("TauIDSFs/python")
from utils import *
from TauIDSFTool import TauIDSFTool, TauESTool, TauFESTool
oldata = "TauIDSFs/data" # if TauIDSFs is not installed in CMSSW environment


def compare_es(id,era,dms=None,gms=None,tag="",verb=0):
  """Compare old (ROOT) vs. new (JSON) ESs."""
  header(f"Compare {id} energy scale tools")
  oldtool1 = TauESTool(era,id+"VSjet",path=oldata) #,verbose=True
  oldtool2 = TauFESTool(era,id+"VSe",path=oldata) #,verbose=True
  oldmeth1 = lambda a: oldtool1.getTES(*a)
  oldmeth2 = lambda a: oldtool2.getFES(*a)
  jname    = f"data/tau/new/tau_es_dm_{id}_{era}{tag}.json"
  cset     = loadeval(jname,rename=id,verb=verb) # wrap to create C++ object that can be evaluated
  assert id in cset, "Did not find ID {id} in cset!"
  newtool  = cset[id]
  dms      = dms or [-1,0,1,2,5,10,11]
  gms      = gms or [0,1,2,3,4,5,6,7]
  pts      = [10.,25.,34.,105.,170.,500.]
  etas     = [-1.0,1.0,2.0,3.0] # barrel: 0-1.5, endcap: 1.5-2.3
  #print(f">>>\n>>> {id}: {newtool.description}")
  #print(f">>> inputs: {newtool.input}")
  head  = "%3s"%("gm")+" ".join("  %-18d"%(d) for d in dms)+"  "
  for pt in pts:
    for eta in etas:
      print(f">>>\n>>> pt={pt}, eta={eta}")
      print(f">>> \033[4m{head}\033[0m")
      for gm in gms:
        #if verb==0 and gm not in [1,3,5]: continue # filter to reduce rows
        row1 = ">>> %3d"%(gm)
        row2 = ">>> "+3*" "
        oldmeth = oldmeth2 if gm in [1,3] else oldmeth1
        for dm in dms:
          args1 = (eta,dm,gm,'All') if gm in [1,3] else (pt,dm,gm,'All')
          args2 = (pt,eta,dm,gm)
          str1, str2 = eval2str(oldmeth,newtool,args1,args2)
          row1 += str1
          row2 += str2
        print(row1)
        print(row2)
  print(">>>")
  

def compare_sfs(id,era,xvar='pt',dms=None,gms=None,tag="",verb=0):
  """Compare old (ROOT) vs. new (JSON) SFs."""
  header(f"Compare {id} SF tools")
  jname   = f"data/tau/new/tau_sf_{xvar}_{id}_{era}{tag}.json"
  cset    = loadeval(jname,rename=id,verb=verb) # wrap to create C++ object that can be evaluated
  assert id in cset, "Did not find ID {id} in cset!"
  newtool  = cset[id]
  dms  = dms or [-1,0,1,2,5,10,11]
  gms  = gms or [0,1,2,3,4,5,6,7]
  pts  = [10.,21.,26.,31.,36.,41.,501.,750.,999.,2000.]
  etas = [-2.0,-1.0,0.0,1.1,2.0,2.5,3.0]
  #print(f">>>\n>>> {id}: {newtool.description}")
  #print(f">>> inputs: {newtool.input}")
  wps = ['Medium','Tight']
  if 'dm' in xvar:
    xbins = dms
    head  = "%3s"%("gm")+" ".join("  %-18d"%(d) for d in dms)+"  "
  elif 'eta' in xvar:
    xbins = etas
    head  = "%3s"%("gm")+" ".join("  %-18.1f"%(e) for e in etas)+"  "
  else:
    xbins = pts
    head  = "%3s"%("gm")+" ".join("  %-18.1f"%(p) for p in pts)+"  "
  for wp in wps:
    print(f">>>\n>>> WP={wp}")
    oldtool = TauIDSFTool(era,id,wp=wp,dm=(xvar=='dm'),path=oldata,verbose=True)
    if 'dm' in xvar:
      oldmeth = lambda a: oldtool.getSFvsDM(*a)
    elif 'eta' in xvar:
      oldmeth = lambda a: oldtool.getSFvsEta(*a)
    else:
      oldmeth = lambda a: oldtool.getSFvsPT(*a)
    print(f">>> \033[4m{head}\033[0m")
    for gm in gms:
      row1 = ">>> %3d"%(gm)
      row2 = ">>> "+3*" "
      for x in xbins:
        args1 = (45.,x,gm,'All') if 'dm' in xvar else (x,gm,'All')
        args2 = (x,gm,wp)
        str1, str2 = eval2str(oldmeth,newtool,args1,args2)
        row1 += str1
        row2 += str2
      print(row1)
      print(row2)
  print(">>>")
  

def main(args):
  global _prec
  outdir    = ensuredir("data/tau/new") #"../data"
  tag       = args.tag # output tag for JSON file
  verbosity = args.verbosity
  dms       = args.dms
  gms       = args.gms
  tids = args.tids or ([ # only run these tau IDs
    #'antiEleMVA6',
    #'antiMu3',
    #'MVAoldDM2017v2',
    #'DeepTau2017v2p1VSe',
    #'DeepTau2017v2p1VSmu',
    'DeepTau2017v2p1VSjet',
  ] if not args.tesids else [ ])
  tesids = args.tesids or ([ # only run these tau ESs
    #'MVAoldDM2017v2',
    'DeepTau2017v2p1',
  ] if not args.tids else [ ])
  eras = args.eras or [ # only run these eras
    #'2016Legacy',
    #'2017ReReco',
    '2018ReReco',
  ]
  if verbosity>=1:
    print(">>> tids = {tids}")
    print(">>> tesids = {tesids}")
    print(">>> eras = {eras}")
  
  # TAU ID SFs
  for id in tids:
    for era in eras:
      xvars = ['eta'] if any(i in id.lower() for i in ['vse','ele','mu']) else ['pt','dm']
      for xvar in xvars:
        compare_sfs(id,era,xvar=xvar,dms=dms,gms=gms,tag=tag,verb=verbosity)
  
  # TAU ENERGY SCALE 
  for id in tesids:
    for era in eras:
      compare_es(id,era,dms=dms,gms=gms,tag=tag,verb=verbosity)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script creates JSON files for hardcoded TauPOG scale factors.'''
  parser = ArgumentParser(prog="tau/convert.py",description=description,epilog="Good luck!")
  parser.add_argument('-t', '--tag',      default="", help="extra tag for JSON output file" )
  parser.add_argument('-I', '--tid',      dest='tids', nargs='+', help="filter by tau ID" )
  parser.add_argument('-E', '--tes',      dest='tesids', nargs='+', help="filter by tau ES" )
  parser.add_argument('-y', '--era',      dest='eras', nargs='+', help="filter by era" )
  parser.add_argument('-d', '--dm',       dest='dms', type=int, nargs='+', help="compare these DMs" )
  parser.add_argument('-g', '--gm',       dest='gms', type=int, nargs='+', help="compare these genmatch" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done!\n")
  
