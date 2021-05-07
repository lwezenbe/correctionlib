#! /usr/bin/env python3
# Author: Izaak Neutelings (May 2021)
# Description: Combine TauPOG Correction JSONs into one master CorrectionSet JSON for central XPOG repo.
# Sources:
#   https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration
#   https://gitlab.cern.ch/cms-tau-pog/jsonpog-integration
# Instructions:
#   scp ineuteli@lxplus.cern.ch:/afs/cern.ch/work/l/lwezenbe/public/TriggerSFs/JSON/*json ./data/tau/new/
#   scripts/tau_combine.py
#   scripts/tau_combine.py a=DeepTauVSmu.json b=DeepTauVSjet.json
import os, sys
import glob
import re
from utils import *


def main(args):
  if args.outdir.endswith(".json"):
    outdir  = ensuredir(os.path.dirname(args.outdir))
    outexp  = args.outdir # output JSON
  else:
    outdir  = ensuredir(args.outdir)
    outexp  = os.path.join(outdir,"tau$ERA$TAG.json") # output JSON
  finnames  = args.finnames
  tag       = args.tag # output tag for JSON file
  eras      = args.eras # eras
  zip       = args.zip
  verbosity = args.verbosity
  
  if finnames:
    header(f"Corrections")
    foutname = outexp.replace('$ERA',"").replace('$TAG',tag) # output JSON
    corrs    = [ ]
    for fname in finnames:
      key = None
      if '=' in fname:
        key = fname.split('=')[0]
        fname = fname[len(key)+1:]
      corr = readjson(fname,rename=key,verb=verbosity)
      corrs.append(corr)
    cset = schema.CorrectionSet(schema_version=schema.VERSION,corrections=corrs)
    print(f">>> Writing {foutname}...")
    JSONEncoder.write(cset,foutname)
    JSONEncoder.write(cset,foutname+".gz")
  else:
    for era in eras:
      header(f"Corrections for {era}")
      foutname = outexp.replace('$ERA','_'+era).replace('$TAG',tag) # output JSON
      finnames = glob.glob(f"data/tau/new/*{era}{tag}.json")+glob.glob(f"data/tau/new/*{era}{tag}.json.gz")
      finexp   = re.compile(r"tau_sf_(pt|eta|dm)_([a-zA-Z0-9]+)_%s%s\.json"%(era,tag))
      corrs    = [ ]
      esfname  = None
      added    = [ ] # prevent overcounting
      for fname in sorted(finnames):
        if "tau_es_" in fname:
          esfname = fname
        if "tau_sf_" not in fname: continue
        if fname in added: continue
        if os.path.basename(fname)==os.path.basename(foutname): continue
        match = finexp.findall(fname)
        if not match:
          print(warn(f"Could not match '{fname}' to {finexp.pattern}! Ignoring..."))
          continue
        #print(">>> ")
        xvar, id = match[0]
        rename = id
        if xvar=='dm':
          rename += "_dm" # DM-dependent VSjet ID
        corr = readjson(fname,rename=rename,verb=verbosity)
        corrs.append(corr)
        added.append(fname)
      if esfname:
        corr = readjson(esfname,rename="tau_energy_scale",verb=verbosity)
        corrs.append(corr)
      cset = schema.CorrectionSet(schema_version=schema.VERSION,corrections=corrs)
      print(f">>> Writing {foutname}...")
      JSONEncoder.write(cset,foutname)
      JSONEncoder.write(cset,foutname+".gz")
    

if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''Combine TauPOG Correction JSONs into one master CorrectionSet JSON for central XPOG repo.'''
  parser = ArgumentParser(prog="tau_combine.py",description=description,epilog="Good luck!")
  parser.add_argument('-o', '--outdir',   default="data/tau/new", help="output direcory or JSON file",
                      metavar='[OUTDIR|OUTFILE]' )
  parser.add_argument('finnames',         nargs='*', help="filenames to combine",
                      metavar='[KEY=]FILE' )
  parser.add_argument('-t', '--tag',      default="", help="extra tag for JSON output file" )
  #parser.add_argument('-I', '--tid',      dest='tids', nargs='+', help="tau ID" )
  #parser.add_argument('-E', '--tes',      dest='tes', nargs='+', help="tau ES" )
  parser.add_argument('-y', '--era',      dest='eras', default=[ ], nargs='+', help="filter by era" )
  parser.add_argument('-z', '--zip',      action='store_true', help="gzip JSON file" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done!\n")
  
