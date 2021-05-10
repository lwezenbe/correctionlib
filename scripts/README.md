More information on the output structure is found in [`data/`](../data/tau).

## Help functions for JSON structure
There are dedicated help functions to implement the particular dependencies and recommendation
of each TauPOG corrections:
* `tau_tid.py` for tau anti-jet efficiency SFs (e.g. `DeepTau2017v2p1VSjet`).
* `tau_ltf.py` for tau anti-lepton fake rate SFs (e.g. `DeepTau2017v2p1VSe/mu`).
* `tau_tid.py` for tau energy scale.
* `tau_convert_trigger.py` for tau trigger SFs & efficiencies.


## Convert old TauPOG SFs
Install `correctionlib`:
```
git clone --recursive git@github.com:nsmith-/correctionlib.git
cd correctionlib
make
pip install .[convert]
```
(possibly with --user, or in a virtualenv, etc.)
Download the TauPOG SFs into [`data/tau`](../data/tau):
```
svn checkout https://github.com/cms-tau-pog/TauIDSFs/trunk/data data/tau/old
```
Run conversion script for each year:
```
./scripts/tau_convert.py -v1 data/tau/old/TauID_SF_pt_DeepTau2017v2p1VSjet_*.root
./scripts/tau_convert.py -v1 data/tau/old/TauID_SF_dm_DeepTau2017v2p1VSjet_*.root
./scripts/tau_convert.py -v1 data/tau/old/TauID_SF_eta_DeepTau2017v2p1VSmu_*.root
./scripts/tau_convert.py -v1 data/tau/old/TauID_SF_eta_DeepTau2017v2p1VSe_*.root
./scripts/tau_convert.py -v1 data/tau/old/Tau[EF]*root
```
The fake rate SFs and tau energy scales were originally hardcoded via the
[`TauIDSFs/utils/createSFFiles.py` script](https://github.com/cms-tau-pog/TauIDSFs/blob/master/utils/createSFFiles.py).
Those can be directly created from the adaptation `tau_createJSONs.py`, e.g.
```
./scripts/tau_createJSONs.py -I DeepTau2017v2p1VSe -y 2016Legacy
./scripts/tau_createJSONs.py -T DeepTau2017v2p1 -y 2016Legacy
```

## Validation
To compare the old (ROOT) and new (JSON) SFs and their respective tools, use
```
git clone https://github.com/cms-tau-pog/TauIDSFs TauIDSFs
./scripts/tau_compare_tools.py -I DeepTau2017v2p1VSjet -y 2018ReReco -g 1 2 5 6
./scripts/tau_compare_tools.py -E DeepTau2017v2p1 -y 2018ReReco -d 0 1 10 11 -g 1 2 5 6
```

## Combination
Once all JSONs are complete, create a master JSON (per year) as follows
```
./scripts/tau_combine.py -y 2018ReReco
```
which will look for all JSONs with name `data/tau/new/tau_*2018ReReco.json`.
Otherwise, specify which to combine:
```
scripts/tau_combine.py a=DeepTauVSmu.json b=DeepTauVSjet.json
```
Copy to the tau repo:
```
scp data/tau/new/*2018ReReco* $USER@lxplus.cern.ch:/eos/cms/store/group/phys_tau/JSONPOG/TauPOG_v2/POG/TAU/2018_ReReco/
```