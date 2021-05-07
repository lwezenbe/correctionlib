#! /usr/bin/env python3
# Author: Izaak Neutelings (May 2021)
# Description: Combine TauPOG Correction JSONs into one master CorrectionSet JSON for central XPOG repo.
# Sources:
#   https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration
#   https://gitlab.cern.ch/cms-tau-pog/jsonpog-integration
# Instructions:
#   scp ineuteli@lxplus.cern.ch:/afs/cern.ch/work/l/lwezenbe/public/TriggerSFs/JSON/*json data/tau/new/
#   scripts/tau_combine.py -y 2018ReReco
#   scripts/tau_combine.py a=DeepTauVSmu.json b=DeepTauVSjet.json
#   scp data/tau/new/*2017* ineuteli@lxplus.cern.ch:/eos/cms/store/group/phys_tau/JSONPOG/POG/TAU/2017_ReReco/
import os, sys
import glob
import re
from datetime import date
from utils import *


def main(args):
  if args.outdir.endswith(".json"):
    outdir  = ensuredir(os.path.dirname(args.outdir))
    outexp  = args.outdir # output JSON
  else:
    outdir  = ensuredir(args.outdir)
    outexp  = os.path.join(outdir,"tau$ERA$TAG.json") # output JSON
  today     = date.today().strftime("%d/%m/%Y")
  finnames  = args.finnames
  tag       = args.tag # output tag for JSON file
  eras      = args.eras # eras
  zip       = args.zip
  validate  = args.validate
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
    if not eras:
      print(">>> Please specify an era you would like to combine, e.g. scripts/tau_combine.py -y 2018ReReco")
    for era in eras:
      header(f"Corrections for {era}")
      info     = f"Correction for simulated tau object, as recommended by the TauPOG for {era}; "+\
                 "tau identification efficiency and fake rate scale factors$IDS, "+\
                 "tau energy scale, and tau trigger scale factors. "+\
                 "For more info, please visit https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendationForRun2"+\
                 " (This file was created on %s)"%(today)
      foutname = outexp.replace('$ERA','_'+era).replace('$TAG',tag) # output JSON
      finname  = f"data/tau/new/*{era}{tag}.json"
      finnames = glob.glob(finname)+glob.glob(finname+".gz")
      finexp   = re.compile(r"tau_sf_(pt-dm|eta)_([a-zA-Z0-9]+)_%s%s\.json"%(era,tag))
      corrs    = [ ]
      esfname  = None
      trgfname = None
      added    = [ ] # prevent overcounting
      ids      = [ ]
      for fname in sorted(finnames):
        basename = os.path.basename(fname)
        if "tau_es_" in basename:
          esfname = fname
        if "tau_trigger_" in basename:
          trgfname = fname
        if "tau_sf_" not in fname: continue
        if fname.replace(".json.gz",".json") in added: continue
        if basename==os.path.basename(foutname): continue
        match = finexp.findall(fname)
        if not match:
          print(warn(f"Could not match '{fname}' to {finexp.pattern}! Ignoring..."))
          continue
        #print(">>> ")
        xvar, id = match[0]
        name = id
        if xvar=='dm':
          rename += "_dm" # DM-dependent VSjet ID
        print(f">>> Adding {green(name)}: {fname}...")
        corr = readjson(fname,rename=name,validate=validate,verb=verbosity)
        corrs.append(corr)
        added.append(fname)
        ids.append(id)
      for fname, name in [(esfname,"tau_energy_scale"),(trgfname,"tau_trigger")]: # add to the end
        if not fname: continue
        print(f">>> Adding {green(name)}: {fname}...")
        corr = readjson(fname,rename=name,validate=validate,verb=verbosity)
        corrs.append(corr)
      if not corrs:
        print(warn("Did not find any valid JSON files {finname}..."))
        continue
      info = info.replace('$IDS'," (%s)"%(', '.join(sorted(ids))))
      print(f">>> Creating CorrectionSet...")
      cset = schema.CorrectionSet(schema_version=schema.VERSION,description=info,corrections=corrs)
      print(f">>> Writing {foutname}...")
      JSONEncoder.write(cset,foutname,maxlistlen=18)
      print(f">>> Writing {foutname}.gz...")
      JSONEncoder.write(cset,foutname+".gz",maxlistlen=18)
    

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
  parser.add_argument('-V', '--validate', action='store_true', help="validate JSON" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  print()
  main(args)
  print(">>> Done!\n")
  
