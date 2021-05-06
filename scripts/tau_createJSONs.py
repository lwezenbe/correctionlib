#! /usr/bin/env python3
# Author: Izaak Neutelings (March 2021)
# Description: Create TauPOG JSON files from hardcoded energy scales & anti-lepton discriminators SFs
# Adapted from https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py
# Instructions:
#   scripts/tau_createJSONs.py -I DeepTau2017v2p1VSe -y 2016Legacy -v1 -t _new
#   scripts/tau_createJSONs.py -I DeepTau2017v2p1VSmu -y 2016Legacy -v1 -t _new
#   scripts/tau_createJSONs.py -T DeepTau2017v2p1 -y 2016Legacy -v1 -t _new
import os, sys
from math import sqrt
from tau_tid import makecorr_tid_dm, makecorr_tid_pt
from tau_ltf import makecorr_ltf
from tau_tes import makecorr_tes, makecorr_tes_id
from utils import *
_prec = 7 # precision


# SF CONTAINER
class SF:
  """Simple container class, that allows for multiplication of SFs
  with correct error propagation."""
  def __init__(self,nom,uncup,uncdn=None,prec=None):
    if prec==None:
      prec = _prec
    if prec<0:
      prec = 10
    if uncdn==None:
      uncdn = uncup
    self.nom   = round(nom,prec)
    self.unc   = round(max(uncup,uncdn),prec)
    self.uncup = round(uncup,prec)
    self.uncdn = round(uncdn,prec)
    self.up    = round(nom+uncup,prec)
    self.dn    = round(nom-uncdn,prec)
  def __mul__(self,osf):
    """Multiply SFs and propagate errors."""
    if isinstance(osf,SF):
      nom   = self.nom*osf.nom
      uncup = nom*sqrt((self.uncup/float(self.nom))**2 + (osf.uncup/float(osf.nom))**2)
      uncdn = nom*sqrt((self.uncdn/float(self.nom))**2 + (osf.uncdn/float(osf.nom))**2)
      return SF(nom,uncup,uncdn)
    return SF(osf*nom,osf*uncup,osf*uncdn) # assume scalar multiplication
  def __len__(self):
    return 3
  def __getitem__(self,index):
    """To act as a list/tuple: nom = sf[0]; uncup = sf[1]; uncdn = sf[2]"""
    if isinstance(index,slice):
      if index.stop!=None and index.stop>3:
        raise IndexError(f"SF only has 3 elements (nom,up,dn), got slice {index}!")
      return (self.nom,self.up,self.dn)[index]
    else:
      if index==0: return self.nom
      elif index==1: return self.up
      elif index==2: return self.dn
      raise IndexError(f"SF only has 3 elements (nom,up,dn), got {index}!")
  #def toJson(self):
  #  return "[%s, %s, %s]"%(self.nom,self.uncup,self.uncdn) #json.dumps((self.nom,self.uncup,self.uncdn))
  def __repr__(self):
    return "SF(%s+%s-%s)"%(self.nom,self.uncup,self.uncdn)
SF0 = SF(0,0) # default 0 +- 0
SF1 = SF(1,0) # default 1 +- 0


def main(args):
  
  global _prec
  outdir    = ensuredir(args.outdir) #"../data"
  tag       = args.tag # output tag for JSON file
  verbosity = args.verbosity
  tidfilter = args.tidfilter or ([ # only run these tau IDs
    'antiEleMVA6',
    'antiMu3',
    'DeepTau2017v2p1VSe',
    'DeepTau2017v2p1VSmu',
  ] if not args.tesfilter else [ ])
  tesfilter = args.tesfilter or ([ # only run these tau ESs
    'MVAoldDM2017v2',
    'DeepTau2017v2p1',
  ] if not args.tidfilter else [ ])
  erafilter = args.erafilter or [ # only run these eras
    '2016Legacy',
    '2017ReReco',
    '2018ReReco',
  ]
  if verbosity>=1:
    print(">>> tidfilter = {tidfilter}")
    print(">>> tesfilter = {tesfilter}")
    print(">>> erafilter = {erafilter}")
  
  
  #######################
  #   ANTI-LEPTON SFs   #
  #######################
  
  _prec = 5
  antiLepSFs     = { }
  antiLepSFs['antiEleMVA6'] = {
    '2016Legacy': { # https://indico.cern.ch/event/828205/contributions/3468902/attachments/1863558/3063927/EtoTauFRLegacy16.pdf
      'VLoose': ( SF(1.175,0.003), SF1, SF(1.288,0.006) ), # LEGACY
      'Loose':  ( SF(1.38, 0.011), SF1, SF(1.24, 0.05 ) ),
      'Medium': ( SF(1.88, 0.04 ), SF1, SF(1.11, 0.10 ) ),
      'Tight':  ( SF(2.16, 0.10 ), SF1, SF(0.91, 0.20 ) ),
      'VTight': ( SF(2.04, 0.16 ), SF1, SF(0.78, 0.31 ) ),
    },
    '2017ReReco': { # https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendation13TeV#Electron_to_tau_fake_rate
      'VLoose': ( SF(1.09,0.01), SF1, SF(1.19,0.01) ),
      'Loose':  ( SF(1.17,0.04), SF1, SF(1.25,0.06) ),
      'Medium': ( SF(1.40,0.12), SF1, SF(1.21,0.26) ),
      'Tight':  ( SF(1.80,0.20), SF1, SF(1.53,0.60) ),
      'VTight': ( SF(1.96,0.27), SF1, SF(1.66,0.80) ),
    },
    '2018ReReco': { # https://indico.cern.ch/event/831606/contributions/3483937/attachments/1871414/3079821/EtoTauFR2018-updated.pdf
      'VLoose': ( SF(1.130,0.005), SF1, SF(1.003,0.005) ), # PRELIMINARY
      'Loose':  ( SF(1.229,0.018), SF1, SF(0.926,0.015) ),
      'Medium': ( SF(1.36, 0.004), SF1, SF(0.91, 0.05 ) ),
      'Tight':  ( SF(1.46, 0.008), SF1, SF(1.02, 0.14 ) ),
      'VTight': ( SF(1.56, 0.16 ), SF1, SF(1.03, 0.24 ) ),
    },
  }
  antiLepSFs['antiMu3'] = {
    '2016Legacy': { # https://indico.cern.ch/event/862376/contributions/3633007/attachments/1942593/3221852/mutauFRRun2_Yiwen.pdf (slide 6)
      'Loose': ( SF(1.106,0.033), SF(1.121,0.034), SF(1.225,0.026), SF(1.115,0.198), SF(2.425,0.229) ),
      'Tight': ( SF(1.274,0.108), SF(1.144,0.231), SF(1.261,0.035), SF(1.159,0.663), SF(3.310,0.554) ),
    },
    '2017ReReco': { # https://twiki.cern.ch/twiki/bin/viewauth/CMS/TauIDRecommendation13TeV#Muon_to_tau_fake_rate
      'Loose': ( SF(1.06,0.05), SF(1.02,0.04), SF(1.10,0.04), SF(1.03,0.18), SF(1.94,0.35) ),
      'Tight': ( SF(1.17,0.12), SF(1.29,0.30), SF(1.14,0.05), SF(0.93,0.60), SF(1.61,0.60) ),
    },
    '2018ReReco': { # https://indico.cern.ch/event/814232/contributions/3397978/attachments/1831354/2999219/mu-tau_FR_2018.pdf
      'Loose': ( SF(1.05,0.05), SF(0.96,0.04), SF(1.06,0.05), SF(1.45,0.08), SF(1.75,0.16) ),
      'Tight': ( SF(1.23,0.05), SF(1.37,0.18), SF(1.12,0.04), SF(1.84,0.32), SF(2.01,0.43) ),
    },
  }
  antiLepSFs['DeepTau2017v2p1VSe'] = {
    # https://indico.cern.ch/event/865792/contributions/3659828/attachments/1954858/3246751/ETauFR-update2Dec.pdf (slides 15, 26, 37)
    '2016Legacy': {
      'VVLoose': ( SF(1.38,0.08), SF1, SF(1.29,0.08) ),
      'VLoose':  ( SF(1.22,0.08), SF1, SF(1.13,0.09) ),
      'Loose':   ( SF(1.28,0.10), SF1, SF(0.99,0.16) ),
      'Medium':  ( SF(1.44,0.13), SF1, SF(1.08,0.21) ),
      'Tight':   ( SF(1.22,0.38), SF1, SF(1.47,0.32) ),
      'VTight':  ( SF(1.52,0.36), SF1, SF(1.59,0.60) ),
      'VVTight': ( SF(2.42,0.43), SF1, SF(2.40,1.04) ),
    },
    '2017ReReco': {
      'VVLoose': ( SF(1.11,0.09), SF1, SF(1.03,0.09) ),
      'VLoose':  ( SF(0.93,0.08), SF1, SF(1.00,0.12) ),
      'Loose':   ( SF(0.96,0.11), SF1, SF(0.91,0.20) ),
      'Medium':  ( SF(1.18,0.20), SF1, SF(0.86,0.21) ),
      'Tight':   ( SF(1.22,0.32), SF1, SF(0.93,0.38) ),
      'VTight':  ( SF(1.18,0.47), SF1, SF(0.95,0.78) ),
      'VVTight': ( SF(0.85,2.39), SF1, SF(1.07,1.41) ),
    },
    '2018ReReco': {
      'VVLoose': ( SF(0.91,0.06), SF1, SF(0.91,0.07) ),
      'VLoose':  ( SF(0.95,0.07), SF1, SF(0.86,0.10) ),
      'Loose':   ( SF(1.06,0.09), SF1, SF(0.78,0.12) ),
      'Medium':  ( SF(1.25,0.14), SF1, SF(0.65,0.15) ),
      'Tight':   ( SF(1.47,0.27), SF1, SF(0.66,0.20) ),
      'VTight':  ( SF(1.79,0.42), SF1, SF(0.91,0.50) ),
      'VVTight': ( SF(2.46,0.90), SF1, SF(0.46,1.00) ),
    },
  }
  antiLepSFs['DeepTau2017v2p1VSmu'] = {
    # https://indico.cern.ch/event/866243/contributions/3650016/attachments/1950974/3238736/mutauFRRun2_Yiwen_20191121.pdf (slides 8-10)
    '2016Legacy': {
      'VLoose': ( SF(0.978,0.029)*SF(1.311,0.057), SF(1.003,0.037)*SF(0.995,0.116), SF(0.992,0.052)*SF(1.275,0.081), SF(1.003,0.037)*SF(0.892,0.156), SF(0.966,0.040)*SF(5.111,0.282) ),
      'Loose':  ( SF(0.978,0.029)*SF(1.411,0.084), SF(1.003,0.037)*SF(0.952,0.210), SF(0.992,0.052)*SF(1.337,0.145), SF(1.003,0.037)*SF(1.037,0.329), SF(0.966,0.040)*SF(6.191,0.386) ),
      'Medium': ( SF(0.978,0.029)*SF(1.442,0.097), SF(1.003,0.037)*SF(0.941,0.272), SF(0.992,0.052)*SF(1.288,0.204), SF(1.003,0.037)*SF(1.054,0.469), SF(0.966,0.040)*SF(5.341,0.616) ),
      'Tight':  ( SF(0.978,0.029)*SF(1.463,0.097), SF(1.003,0.037)*SF(0.722,0.289), SF(0.992,0.052)*SF(1.337,0.239), SF(1.003,0.037)*SF(0.966,0.650), SF(0.966,0.040)*SF(5.451,0.846) ),
    },
    '2017ReReco': {
      'VLoose': ( SF(0.979,0.033)*SF(1.117,0.067), SF(0.953,0.034)*SF(0.952,0.070), SF(0.983,0.037)*SF(0.952,0.070), SF(0.988,0.038)*SF(0.744,0.126), SF(1.004,0.052)*SF(4.592,0.247) ),
      'Loose':  ( SF(0.979,0.033)*SF(1.076,0.112), SF(0.953,0.034)*SF(0.940,0.140), SF(0.983,0.037)*SF(0.940,0.140), SF(0.988,0.038)*SF(0.916,0.272), SF(1.004,0.052)*SF(5.596,0.422) ),
      'Medium': ( SF(0.979,0.033)*SF(1.062,0.149), SF(0.953,0.034)*SF(0.819,0.206), SF(0.983,0.037)*SF(0.819,0.206), SF(0.988,0.038)*SF(1.021,0.375), SF(1.004,0.052)*SF(4.235,0.617) ),
      'Tight':  ( SF(0.979,0.033)*SF(0.991,0.152), SF(0.953,0.034)*SF(0.675,0.259), SF(0.983,0.037)*SF(0.675,0.259), SF(0.988,0.038)*SF(1.098,0.457), SF(1.004,0.052)*SF(4.175,0.779) ),
    },
    '2018ReReco': {
      'VLoose': ( SF(0.936,0.040)*SF(1.019,0.060), SF(0.874,0.028)*SF(1.154,0.106), SF(0.912,0.030)*SF(1.128,0.073), SF(0.953,0.040)*SF(0.974,0.147), SF(0.936,0.038)*SF(5.342,0.339) ),
      'Loose':  ( SF(0.936,0.040)*SF(0.993,0.097), SF(0.874,0.028)*SF(1.371,0.202), SF(0.912,0.030)*SF(1.165,0.135), SF(0.953,0.040)*SF(0.860,0.265), SF(0.936,0.038)*SF(6.631,0.473) ),
      'Medium': ( SF(0.936,0.040)*SF(0.940,0.120), SF(0.874,0.028)*SF(1.519,0.269), SF(0.912,0.030)*SF(1.032,0.193), SF(0.953,0.040)*SF(0.817,0.392), SF(0.936,0.038)*SF(5.597,0.691) ),
      'Tight':  ( SF(0.936,0.040)*SF(0.820,0.130), SF(0.874,0.028)*SF(1.436,0.292), SF(0.912,0.030)*SF(0.989,0.220), SF(0.953,0.040)*SF(0.875,0.434), SF(0.936,0.038)*SF(4.739,0.848) ),
    },
  }
  
  # CREATE JSON
  antiEleEtaBins = ( 0.0, 1.460, 1.558, 2.3 )
  antiMuEtaBins  = ( 0.0, 0.4, 0.8, 1.2, 1.7, 2.3 )
  for id in antiLepSFs:
    if id not in tidfilter: continue
    ltype = 'mu' if 'mu' in id.lower() else 'e'
    for era in antiLepSFs[id]:
      if era not in erafilter: continue
      sfs   = antiLepSFs[id][era] # WP -> (nom,uncup,uncdn)
      ebins = antiEleEtaBins if any(s in id for s in ['antiEle','VSe']) else antiMuEtaBins
      if verbosity>0:
        print(f">>> etabins={ebins}")
        print(f">>> sfs={sfs}")
      corr = makecorr_ltf(sfs,id=id,era=era,ltype=ltype,bins=ebins,
                          outdir=outdir,tag=tag,verb=verbosity)
  
  
  ########################
  #   TAU ENERGY SCALE   #
  ########################
  
  # TAU ENERGY SCALES low pT (Z -> tautau)
  tesvals = { }
  _prec   = 7
  
  # TAU ENERGY SCALES low pT (Z -> tautau)
  tesvals['low'] = { # units of percentage (centered around 0.0)
    'MVAoldDM2017v2': {
      '2016Legacy': { 0: (-0.6,1.0), 1: (-0.5,0.9), 10: ( 0.0,1.1), 11: ( 0.0,1.1), },
      '2017ReReco': { 0: ( 0.7,0.8), 1: (-0.2,0.8), 10: ( 0.1,0.9), 11: (-0.1,1.0), },
      '2018ReReco': { 0: (-1.3,1.1), 1: (-0.5,0.9), 10: (-1.2,0.8), 11: (-1.2,0.8), },
    },
    # https://indico.cern.ch/event/887196/contributions/3743090/attachments/1984772/3306737/TauPOG_TES_20200210.pdf
    'DeepTau2017v2p1': {
      '2016Legacy': { 0: (-0.9,0.8), 1: (-0.1,0.6), 10: ( 0.3,0.8), 11: (-0.2,1.1), },
      '2017ReReco': { 0: ( 0.4,1.0), 1: ( 0.2,0.6), 10: ( 0.1,0.7), 11: (-1.3,1.4), },
      '2018ReReco': { 0: (-1.6,0.9), 1: (-0.4,0.6), 10: (-1.2,0.7), 11: (-0.4,1.2), },
    },
  }
  for id in tesvals['low']:
    if id not in tesfilter: continue
    for era in tesvals['low'][id]:
      if era not in erafilter: continue
      for dm, (tes,unc) in tesvals['low'][id][era].items():
        tesvals['low'][id][era][dm] = SF(1.+tes/100.,unc/100.) # convert percentage back to scale factor
  
  # TAU ENERGY SCALES at high pT (W* + jets)
  tesvals['high'] = { # scale factor centered around 1.
    'MVAoldDM2017v2': { # central values from Z -> tautau measurement
      '2016Legacy': { 0: SF(0.991,0.030), 1: SF(0.995,0.030), 10: SF(1.000,0.030), 10: SF(1.000,0.030), }, # reuse DM10 for DM11
      '2017ReReco': { 0: SF(1.004,0.030), 1: SF(0.998,0.030), 10: SF(1.001,0.030), 10: SF(1.001,0.030), },
      '2018ReReco': { 0: SF(0.984,0.030), 1: SF(0.995,0.030), 10: SF(0.988,0.030), 10: SF(0.988,0.030), },
    },
    # https://indico.cern.ch/event/871696/contributions/3687829/attachments/1968053/3276394/TauES_WStar_Run2.pdf
    'DeepTau2017v2p1': {
      '2016Legacy': { 0: SF(0.991,0.030), 1: SF(1.042,0.020), 10: SF(1.004,0.012), 11: SF(0.970,0.027), },
      '2017ReReco': { 0: SF(1.004,0.030), 1: SF(1.014,0.027), 10: SF(0.978,0.017), 11: SF(0.944,0.040), },
      '2018ReReco': { 0: SF(0.984,0.030), 1: SF(1.004,0.020), 10: SF(1.006,0.011), 11: SF(0.955,0.039), },
    },
  }
  
  # TAU ENERGY SCALES for e -> tau_h fakes (Olena)
  tesvals['ele'] = { # scale factor centered around 1.
    'DeepTau2017v2p1': {
      '2016Legacy': { # barrel / endcap
        0: [SF(1.00679,0.806/100.,0.982/100.), SF(0.965,  1.808/100.,1.102/100.)],
        1: [SF(1.03389,1.168/100.,2.475/100.), SF(1.05,   6.570/100.,5.694/100.)],
      },
      '2017ReReco': {
        0: [SF(1.00911,1.343/100.,0.882/100.), SF(0.97396,2.249/100.,1.430/100.)],
        1: [SF(1.01154,2.162/100.,0.973/100.), SF(1.015,  6.461/100.,4.969/100.)],
      },
      '2018ReReco': {
        0: [SF(1.01362,0.904/100.,0.474/100.), SF(0.96903,3.404/100.,1.250/100.)],
        1: [SF(1.01945,1.226/100.,1.598/100.), SF(0.985,  5.499/100.,4.309/100.)],
      },
    }
  }
  tesvals['ele']['MVAoldDM2017v2'] = tesvals['ele']['DeepTau2017v2p1'] # reuse DeepTau2017v2p1 ESs for MVAoldDM2017v2
  
  # CREATE JSON
  ptbins  = (0.,34.,170.)
  etabins = (0.,1.5,2.5)
  tesids  = [id for id in tesvals['low'].keys()]
  teseras = [e for e in tesvals['low'][tesids[0]].keys()]
  for era in teseras:
    if era not in erafilter: continue
    tesvals_ = { } # swap order: era -> id -> type -> dm (-> eta bin)
    for id in tesids:
      if id not in tesfilter: continue
      assert era in tesvals['high'][id], f"Did not find {era} for {id} high-pT tau energy scale!"
      assert era in tesvals['ele'][id],  f"Did not find {era} for {id} electron fake tau energy scale!"
      tesvals_[id] = {
        'low':  tesvals['low'][id][era],
        'high': tesvals['high'][id][era],
        'ele':  tesvals['ele'][id][era],
      }
      for key in tesvals_[id]:
        reusesf(tesvals_[id][key], 1, 2) # reuse DM1 for DM2
        reusesf(tesvals_[id][key],10,11) # reuse DM10 for DM11 (if DM10 exists)
    if verbosity>=1:
      print(">>> tesvals={")
      for id in tesvals_:
        print(f">>>   '{id}': {{")
        for key in tesvals_[id]:
          print(f">>>     '{key}': {tesvals_[id][key]}")
        print(">>>   }")
      print(">>> }")
    corr = makecorr_tes(tesvals_,era=era,ptbins=ptbins,etabins=etabins,
                        outdir=outdir,tag=tag,verb=verbosity)
  ###tesids  = tesvals['low'].keys()
  ###for id in tesids:
  ###  if id not in tesfilter: continue
  ###  assert id in tesvals['high'], f"Did not find {id} for high-pT tau energy scale!"
  ###  assert id in tesvals['ele'],  f"Did not find {id} for electron fake tau energy scale!"
  ###  teseras = tesvals['low'][id].keys()
  ###  for era in teseras:
  ###    assert era in tesvals['high'][id], f"Did not find {era} for {id} high-pT tau energy scale!"
  ###    assert era in tesvals['ele'][id],  f"Did not find {era} for {id} electron fake tau energy scale!"
  ###    if era not in erafilter: continue
  ###    tesvals_ = { # swap order: id -> era -> type -> dm (-> eta bin)
  ###      'low':  tesvals['low'][id][era],
  ###      'high': tesvals['high'][id][era],
  ###      'ele':  tesvals['ele'][id][era],
  ###    }
  ###    for key in tesvals_:
  ###      reusesf(tesvals_[key], 1, 2) # reuse DM1 for DM2
  ###      reusesf(tesvals_[key],10,11) # reuse DM10 for DM11 (if DM10 exists)
  ###    if verbosity>0:
  ###      print(f">>> tesvals={tesvals_}")
  ###    corr = makecorr_tes_id(tesvals_,id=id,era=era,ptbins=ptbins,etabins=etabins,
  ###                           outdir=outdir,tag=tag,verb=verbosity)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script creates JSON files for hardcoded TauPOG scale factors.'''
  parser = ArgumentParser(prog="tau_createJSONs.py",description=description,epilog="Good luck!")
  parser.add_argument('-o', '--outdir',   default="data/tau/new", help="output direcory for JSON file" )
  parser.add_argument('-t', '--tag',      default="", help="extra tag for JSON output file" )
  parser.add_argument('-I', '--tid',      dest='tidfilter', nargs='+', help="filter by tau ID" )
  parser.add_argument('-E', '--tes',      dest='tesfilter', nargs='+', help="filter by tau ES" )
  parser.add_argument('-y', '--era',      dest='erafilter', nargs='+', help="filter by era" )
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print(">>> Done!")
  
