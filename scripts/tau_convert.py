#! /usr/bin/env python3
# Author: Izaak Neutelings (January 2021)
# Description: Script to play around with different formats, writing, reading, evaluating and validating.
# Instructions: Download old SF files and run:
#   svn checkout https://github.com/cms-tau-pog/TauIDSFs/trunk/data data/tau/old
#   ./scripts/tau_convert.py data/tau/old/*root -v1
# Sources:
#   https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
#   https://github.com/cms-nanoAOD/correctionlib/blob/master/tests/test_core.py
import sys; sys.path.append('scripts')
from utils import *
from tau_tid import makecorr_tid_dm, makecorr_tid_pt
from tau_ltf import makecorr_ltf
from tau_tes import makecorr_tes
import re
from ROOT import gROOT, TFile
rexp_fjet = re.compile(r"(?:.+/)?TauID_SF_([^_]+)_([^_]+)_(20[0123][^_]+)(\w*).root$")
rexp_ftes = re.compile(r"(?:.+/)?TauF?ES_([^_]+)_([^_]+)_(20[0123][^_]+)(\w*).root$")
rexp_era  = re.compile(r"(?<=_)20[0123]\d(?!v\d)[^_.]+")
rexp_num  = re.compile(r"[-+]?\d+\.?\d*")
rexp_tid  = re.compile(r"\(([^)&]+)(?:&&)?([^)&]*)\)\*([-+]*[\d.]+|\([^)]+\))") # "(x<=25)*1.0+(x>20&&x<=25)*1.0+..."


def main(args):
  fnames    = args.fnames
  verbosity = args.verbosity
  prec      = 7 # precision of SFs
  lprec     = 5 # precision of l -> tau_h SFs
  infiles   = {
    'jet': { }, # DM/pT-dependent DeepTauVSjet, MVAoldDM: era -> id -> jet/dm -> fname
    'mu':  { }, # eta-dependent DeepTauVSmu:              era -> id -> fname
    'e':   { }, # eta-dependent DeepTauVSe:               era -> id -> fname
    'tes': { }, # eta/DM-dependent tau energy scale:      era -> id -> low/high/ele -> fname
  }
  
  # CATEGORIZED
  for fname in fnames:
    if not fname.lower().endswith(".root"):
      print(f">>> {fname}: Not a ROOT file! Ignoring...")
      continue
    if fname.endswith("_EMB.root"):
      print(f">>> {fname}: Ignoring embedded SFs for now...")
      continue
    match = rexp_fjet.match(fname)
    if match:
      param, id, era, tag = match.groups()
      if param=='pt': #fname.startswith("TauID_SF_pt_"):
        infiles['jet'].setdefault(era,{ }).setdefault(id,{ })['pt'] = fname
        continue
      elif param=='dm': #fname.startswith("TauID_SF_dm_"):
        infiles['jet'].setdefault(era,{ }).setdefault(id,{ })['dm'] = fname
        continue
      elif param=='eta' and any(x in id for x in ['VSe','Ele']):
        infiles['e'].setdefault(era,{ })[id] = fname
        continue
      elif param=='eta' and any(x in id for x in ['VSmu','Mu']):
        infiles['mu'].setdefault(era,{ })[id] = fname
        continue
    match = rexp_ftes.match(fname)
    if match:
      param, id, era, tag = match.groups()
      if 'VS' in id:
        id = id[:id.index('VS')]
      if param=='dm' and tag=='': # DM-dependent tau energy scale for real tau_h, low pT
        infiles['tes'].setdefault(era,{ }).setdefault(id,{ })['low'] = fname
        continue
      elif param=='dm' and 'ptgt100' in tag: # DM-dependent tau energy scale for real tau_h, high pT
        infiles['tes'].setdefault(era,{ }).setdefault(id,{ })['high'] = fname
        continue
      elif param=='eta-dm': # eta/DM-dependent tau energy scale for e -> tau_h fake
        infiles['tes'].setdefault(era,{ }).setdefault(id,{ })['ele'] = fname
        continue
    print(f">>> {fname}: Did not recognize file! Ignoring...")
  for era in infiles['tes']: # reuse e -> tau_h ES from DeepTau
    for id in infiles['tes'][era]:
      if "DeepTau" not in id and 'ele' not in infiles['tes'][era][id] and\
         infiles['tes'][era].get("DeepTau2017v2p1",{ }).get('ele',False):
        infiles['tes'][era][id]['ele'] = infiles['tes'][era]["DeepTau2017v2p1"]['ele']
  if verbosity>0:
    print(JSONEncoder.dumps(infiles)) # print all categorized files
  
  # TAU ANTI-JET SFs
  for era in infiles['jet']:
    for id in infiles['jet'][era]:
      if 'dm' in infiles['jet'][era][id]: # DM-dependent
        print(f">>> {era}: DM-dependent {id} SFs from {fname}")
        fname = infiles['jet'][era][id]['dm']
        file = TFile.Open(fname)
        sfs = { } # wp -> dm -> (sf,up,down)
        for key in file.GetListOfKeys():
          if not gROOT.GetClass(key.GetClassName()).InheritsFrom('TH1'): continue
          wp      = key.GetName()
          hist    = file.Get(wp)
          sfs[wp] = { }
          for dm in [0,1,2,5,6,10,11]:
            bin  = hist.GetXaxis().FindBin(dm)
            sf   = hist.GetBinContent(bin)
            if sf<=0: continue
            err  = hist.GetBinError(bin)
            sfup = round(sf+err,prec)
            sfdn = round(sf-err,prec)
            sf   = round(sf,prec)
            sfs[wp][dm] = (sf,sfup,sfdn)
          if 1 in sfs[wp] and 2 not in sfs[wp]: # reuse DM1 for DM2
            sfs[wp][2] = sfs[wp][1]
        file.Close()
        if verbosity>0:
          print(JSONEncoder.dumps(sfs))
        corr = makecorr_tid_dm(sfs,id=id,era=era,verb=verbosity)
      elif 'pt' in infiles['jet'][era][id]: # pT-dependent
        fname = infiles['jet'][era][id]['pt']
        print(f">>> {era}: pT-dependent {id} SFs from {fname}")
        file = TFile.Open(fname)
        sfs = { }
        for key in file.GetListOfKeys():
          if not gROOT.GetClass(key.GetClassName()).InheritsFrom('TF1'): continue
          if not key.GetName().endswith('_cent'): continue
          wp      = key.GetName().replace("_cent","")
          if not any(w==wp.lstrip('V') for w in ['Loose','Medium','Tight']): continue
          if not wp=='Medium': continue
          wpnom   = key.GetName()
          wpup    = key.GetName().replace("cent","up")
          wpdown  = key.GetName().replace("cent","down")
          fnom    = rexp_tid.findall(str(file.Get(wpnom).GetExpFormula()).replace(' ',''))
          fup     = rexp_tid.findall(str(file.Get(wpup).GetExpFormula()).replace(' ',''))
          fdown   = rexp_tid.findall(str(file.Get(wpdown).GetExpFormula()).replace(' ',''))
          ptbins  = [ ]
          sfs[wp] = [ ]
          xmax    = -1
          if verbosity>0:
            print(">>> fnom  = %r"%(fnom))
            print(">>> fup   = %r"%(fup))
            print(">>> fdown = %r"%(fdown))
          assert len(fnom)==len(fup)-2 and len(fnom)==len(fdown)-2, "Number of bins does not match: %s, %s, %s"%(fnom,fup,fdown)
          for snom, sup, sdown in zip(fnom,fup,fdown):
            if snom[2].replace('.','',1).isdigit() and float(snom[2])<=0: continue
            assert "x>" in snom[0] and (snom[1]=='' or "x<" in snom[1]), "Did not recognize bin in %r"%(snom)
            assert snom[0]==sup[0] and (snom[1]=='' or snom[1]==sup[1]), "Bins upper SFs do not match: %r vs. %r"%(snom,sup)
            assert snom[0]==sdown[0] and (snom[1]=='' or snom[1]==sdown[1]), "Bins lower SFs do not match: %r vs. %r"%(snom,sdown)
            xmin   = float(rexp_num.findall(snom[0])[0])
            assert xmax<0 or xmax==xmin, "pT bins not in increasing order!"
            sf     = float(snom[2])
            sfup   = round(float(sup[2])-sf,prec)
            sfdn   = round(sf-float(sdown[2]),prec)
            sf     = round(sf,prec)
            sfs[wp].append((sf,sfup,sfdn))
            ptbins.append(xmin)
            if snom[1]!='':
              xmax = float(rexp_num.findall(snom[1])[0]) # get upper edge to compare to next bin's lower edge
          assert xmax<500., "Last central SF bin >=500: %r"%(fnom)
          assert "500" in fup[-2][0] and "1000" in fup[-1][0], "Last bins are not [500,1000]: {fup[-2:]}"
          assert "500" in fdown[-2][0] and "1000" in fdown[-1][0], "Last bins are not [500,1000]: {fdown[-2:]}"
          lastup1 = sfs[wp][-1][0]+2*sfs[wp][-1][1]
          lastdn1 = sfs[wp][-1][0]-2*sfs[wp][-1][2]
          lastup2 = sum(float(x) for x in rexp_num.findall(fup[-1][2]))
          lastdn2 = sum(float(x) for x in rexp_num.findall(fdown[-1][2]))
          assert abs(lastup1-lastup2)<10**(1-prec), "Upper error in SF in last bin is not 2x that of previous bin: %s, %s"%(lastup1,lastup2)
          assert abs(lastdn1-lastdn2)<10**(1-prec), "Lower error in SF in last bin is not 2x that of previous bin: %s, %s"%(lastdn1,lastdn2)
          ptbins += [500.,1000.,2000.]
          sfs[wp].append(sfs[wp][-1]) #  500 < pt < 1000
          sfs[wp].append(sfs[wp][-1]) # 1000 < pt < 2000
        if verbosity>0:
          print(f">>> ptbins={ptbins}")
          print(JSONEncoder.dumps(sfs))
        corr = makecorr_tid_pt(sfs,id=id,era=era,verb=verbosity)
        file.Close()
  
  # TAU ANTI-ELECTRON SFs
  for ltype in ['e','mu']:
    from tau_tid import makecorr_tid_pt
    for era in infiles[ltype]:
      for id in infiles[ltype][era]:
        fname = infiles[ltype][era][id]
        print(f">>> {era}: eta-dependent {id} SFs from {fname}")
        file = TFile.Open(fname)
        sfs = { } # wp -> (sf,up,down)
        for key in file.GetListOfKeys():
          if not gROOT.GetClass(key.GetClassName()).InheritsFrom('TH1'): continue
          wp      = key.GetName()
          hist    = file.Get(wp)
          ebins   = [hist.GetXaxis().GetBinLowEdge(1)]
          sfs[wp] = [ ]
          for bin in range(1,hist.GetXaxis().GetNbins()+1):
            low  = hist.GetXaxis().GetBinLowEdge(bin)
            up   = hist.GetXaxis().GetBinUpEdge(bin)
            assert ebins[-1]==low, f"Bins do not match: {ebins[-1]}!={low}, {ebins}"
            ebins.append(up)
            sf   = hist.GetBinContent(bin)
            if sf<=0: continue
            err  = hist.GetBinError(bin)
            sfup = round(sf+err,lprec)
            sfdn = round(sf-err,lprec)
            sf   = round(sf,lprec)
            sfs[wp].append((sf,sfup,sfdn))
        file.Close()
        if verbosity>0:
          print(f">>> etabins={ebins}")
          print(JSONEncoder.dumps(sfs))
        corr = makecorr_ltf(sfs,id=id,era=era,ltype=ltype,bins=ebins,verb=verbosity)
        exit(0)
  
  # TAU ENERGY SCALES
  for era in infiles['tes']:
    for id in infiles['tes'][era]:
      assert all(k in infiles['tes'][era][id] for k in ['low','high','ele']), f"Not all files are present: {infiles['tes'][era][id]}"
      fnames = infiles['tes'][era][id]
      print(f">>> {era}: {id} energy scales from\n>>>   "+"\n>>>   ".join(fnames.values()))
      tesvals = {
        'low':  { }, # DM-dependent, low pT, real tau_h
        'high': { }, # DM-dependent, high pT, real tau_h
        'ele':  { }, # DM-/eta-dependent, e -> tau_h
      }
      ptbins  = [0.,34.,170.]
      etabins = [0.,1.5,2.5]
      for key, fname in fnames.items():
        file = TFile.Open(fname)
        if key=='ele':
          # See
          #  https://github.com/cms-tau-pog/TauIDSFs/blob/127e021f1616f1480837a62742b775cd42bcc9ac/utils/createSFFiles.py#L111-L117
          #  https://github.com/cms-tau-pog/TauIDSFs/blob/127e021f1616f1480837a62742b775cd42bcc9ac/python/TauIDSFTool.py#L216-L222
          file.ls()
          graph = file.Get('fes')
          i = 0
          print(list(graph.GetY()))
          for region in ['barrel','endcap']: # eta in [0.,1.5,2.5]
            for dm in [0,1]:
              fes   = graph.GetPointY(i)
              fesup = round(fes+graph.GetErrorYhigh(i),prec)
              fesdn = round(fes-graph.GetErrorYlow(i),prec)
              fes   = round(graph.GetPointY(i),prec)
              tesvals[key].setdefault(dm,[ ]).append((fes,fes+fesup,fes-fesdn))
              i += 1
          tesvals[key][2] = tesvals[key][1][:] # reuse DM1 for DM2
        else:
          hist = file.Get('tes')
          for dm in [0,1,2,5,6,10,11]:
            bin  = hist.GetXaxis().FindBin(dm)
            tes   = hist.GetBinContent(bin)
            err   = hist.GetBinError(bin)
            if tes<=0 or (tes==1.0 and err==0.0): continue
            tesup = round(tes+err,prec)
            tesdn = round(tes-err,prec)
            tes   = round(tes,prec)
            tesvals[key][dm] = (tes,tesup,tesdn)
          if 1 in tesvals[key] and 2 not in tesvals[key]: # reuse DM1 for DM2
            tesvals[key][2] = tesvals[key][1]
        file.Close()
      if verbosity>0:
        #print(f">>> etabins={ebins}")
        print(JSONEncoder.dumps(tesvals))
      corr = makecorr_tes(tesvals,id=id,era=era,ptbins=ptbins,etabins=etabins,verb=verbosity)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script creates datacards with CombineHarvester.'''
  parser = ArgumentParser(prog="tau/convert.py",description=description,epilog="Succes!")
  parser.add_argument('fnames',           nargs='+', action='store', help="file names" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print()
  
