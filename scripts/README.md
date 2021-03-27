More information on the output structure is found in [`data/`](../data/tau).

## Convert TauPOG SFs

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