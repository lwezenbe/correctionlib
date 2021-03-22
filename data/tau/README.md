# TauPOG Corrections

These are the JSON files for the TauPOG. The are created with the scripts in [`scripts/`](../../scripts).


## Summary of available DeepTau SFs

This is a rough summary of the available SFs for `DeepTau2017v2p1` from the [official TauPOG SF tool](https://github.com/cms-tau-pog/TauIDSFs/tree/master/data)

| Tau component  | `genmatch`  | `DeepTau2017v2p1` `VSjet`  | `DeepTau2017v2p1` `VSe`  | `DeepTau2017v2p1` `VSmu`  | energy scale   |
|:--------------:|:-----------:|:--------------------------:|:------------------------:|:-------------------------:|:--------------:|
| real tau       | `5`         | vs. pT, or vs. DM          | –                        | –                         | vs. DM         |
| e -> tau fake  | `1`, `3`    | –                          | vs. eta                  | –                         | vs. DM and eta |
| mu -> tau fake | `2`, `4`    | –                          | –                        | vs. eta                   | – (±1% unc.)   |

## Structure of main JSON file:
One correction set with correction object per year and ID. See [XPOG repository](https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/blob/master/README.md).
```
JSON
└─year
  └─ ID (e.g. DeepTau2017v2p1VSjet, DeepTau2017v2p1VSe, energy scale, ...)
```


## Structure of e -> tau fake rate SFs
One correction object per year and ID.
```
year
└─ ID (antiEle, DeepTau2017v2p1VSe)
   └─ category:genmatch (0-5)
      ├─ key:genmatch==1,3 (e -> tau fake)
      │  └─ category:wp
      │     └─ transform:eta (eta -> abs(eta))
      │        └─ binned:eta
      │           └─ category:syst (nom, up, down)
      │              └─ float:sf
      └─ key:default (genmatch!=1,3)
         └─ float:1.0
```


## Structure of mu -> tau fake rate SFs
One correction object per year and ID.
```
year
└─ ID (antiMu, DeepTau2017v2p1VSmu)
   └─ category:genmatch (0-5)
      ├─ key:genmatch==2,4 (mu -> tau fake)
      │  └─ category:wp
      │     └─ transform:eta (eta -> abs(eta))
      │        └─ category:syst (nom, up, down)
      │           └─ binned:abseta
      │              └─ float:sf
      └─ key:default (genmatch!=2,4)
         └─ float:1.0
```


## Structure of real tau efficiency rate SFs
One correction object per year and ID.
Users can choose either pT- __or__ DM-dependent SFs.
```
year
├─ ID, pT-dependent (MVAoldDM2017v2, DeepTau2017v2p1VSjet)
│  └─ category:genmatch (0-5)
│     ├─ key:genmatch==5 (real tau)
│     │  └─ category:wp
│     │     └─ binning:pt
│     │       └─ category:syst (nom, up, down)
│     │          ├─ key:nom
│     │          │  └─ float:sf
│     │          ├─ key:up
│     │          │  ├─ formula:sf (500<pt<1000)
│     │          │  └─ float:sf (otherwise)
│     │          └─ key:down
│     │             ├─ formula:sf (500<pt<1000)
│     │             └─ float:sf (otherwise)
│     └─ key:default (genmatch!=5)
│        └─ float:1.0
└─ ID, DM-dependent (e.g. MVAoldDM2017v2, DeepTau2017v2p1VSjet)
   └─ category:genmatch (0-5)
      ├─ key:genmatch==5 (real tau)
      │  └─ category:wp
      │     └─ category:syst (nom, up, down)
      │        └─ float:sf
      └─ key:default (genmatch!=5)
         └─ float:1.0
```

<p align="center">
  <img src="../../docs/tau/Tau_SF_vs_pt.gif" alt="Tau DeepTau2017v2VSjet efficiency SF" width="380"/>
</p>


## Structure of tau energy scales
One correction object per year and ID.
```
year
└─ ID (MVAoldDM2017v2, DeepTau2017v2p1VSjet)
   └─ category:genmatch
      ├─ key:genmatch==5 (real tau)
      │  └─ category:dm
      │     ├─ key:dm==0,1,10,11
      │     │  └─ binning:pt
      │     │     └─ category:syst (nom, up, down)
      │     │        ├─ key:nom
      │     │        │  └─ float:sf
      │     │        ├─ key:up
      │     │        │  ├─ formula:sf (34<pt<170)
      │     │        │  └─ float:sf (otherwise)
      │     │        └─ key:down
      │     │           ├─ formula:sf (34<pt<170)
      │     │           └─ float:sf (otherwise)
      │     └─ key:default
      │        └─ float:1.0
      ├─ key:genmatch==1,3 (e -> tau fake)
      │  └─ category:dm
      │     ├─ key:dm==0,1
      │     │  └─ binned:eta
      │     │     └─ category:syst (nom, up, down)
      │     │        └─ float:sf
      │     └─ key:default
      │        └─ float:1.0
      ├─ key:genmatch==2,4 (mu -> tau fake)
      │  └─ category:syst (nom, up, down)
      │     └─ float:sf
      └─ key:default (j -> tau fake)
         └─ float:1.0
```

<p align="center">
  <img src="../../docs/tau/TESunc.png" alt="Tau energy scale uncertainty treatment" width="380"/>
</p>


## Structure of tau triggers
TBA.
