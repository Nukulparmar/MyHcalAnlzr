# MyHcalAnlzr - HCAL Pedestal Analysis Framework

A comprehensive analysis framework for processing HCAL calibration run data, generating pedestal histograms over lumi and/or by days. 

## Overview
Currently works the best for making pedestal plots for the whole run. For the wholeFill it might work out of the box but will require fixing some hardcoded values eg. ```makePlot.sh```. Also the condor setup to submit the jobs for creating the HCAL Nanos is not created yet (it is easy to include this setup but I have not done this in the interest of time). 

**Remember**: Always update storage paths from `nparmar` to your own username before running!


## Workflow

```
Raw Data Files → NanoAOD → Per-LS ROOT files → Summary Histograms/SaveFile.txt → Pedestal Plots
     ↓              ↓              ↓                           ↓                        ↓
FindDatasetToRun  cmsRun    digi_fromNano.cc            digi_process.py             Plotting.py
```

### Step-by-Step Process

1. **Find Dataset**: `FindDatasetToRun.py` discovers files for specified runs/dates
2. **Create NanoAOD**: `cmsDriver` + `cmsRun` produces HCAL NanoAOD tuples
3. **Extract Pedestals**: `digi_fromNano.cc` creates per-LS histograms (~35 MB each)
4. **Summarize**: `digi_process.py` generates summary histograms (~103 KB each)
5. **Plot**: `Plotting.py` creates pedestal trend plots and save them in the eos space.

---

## Directory Structure

```
MyHcalAnlzr/
├── FindDatasetToRun.py          # Main entry point for dataset discovery and job submission
├── digi_fromNano.cc             # C++ analyzer: creates per-LS pedestal histograms
├── digi_process.py              # Python: processes per-LS files → summaries
├── Plotting.py                  # Plotting and DPG table generation
├── MakeSmall.py                 # Reduces NanoAOD file size by removing branches
├── compile.sh                   # Compiles digi_fromNano.cc
├── HcalNano_Template_condor.sh  # Condor job template
├── condor_*.jdl                 # Condor submission files
├── ref_table.txt                # Reference channel table (all HCAL channels)
├── lmap_complete.txt            # Logical map for HCAL channels
├── plugins/                     # CMSSW EDAnalyzer plugins
│   ├── MyHcalAnlzr.cc          # Main HCAL analyzer
│   └── BuildFile.xml
├── python/                      # CMSSW Python configs
│   ├── localrun_singleFull.py
│   └── localrun_singlePed.py
├── condor_out_*/                # Condor job outputs
└── WholeRunOutput_*/            # Per-run output directories
```

---

## Prerequisites

### Software Requirements
- **CMSSW**: Get the latest CMSSW version according to the files to be analyzed
- **ROOT**: Version 6.x (included with CMSSW)
- **Python**: 3.6+


### Setup Environment
```bash
# On lxplus
cd /afs/cern.ch/user/X/YOURUSER/public/
source /cvmfs/cms.cern.ch/cmsset_default.sh

# Setup CMSSW
cmsrel CMSSW_15_1_0
cd CMSSW_15_1_0/src
cmsenv
git init 

# Clone or copy MyHcalAnlzr
git clone git@github.com:Nukulparmar/MyHcalAnlzr.git
cd MyHcalAnlzr/MyHcalAnlzr
# switch to the branch hcalNano_WholeFill
scram b -j 4

# Compile the C++ analyzer
. compile.sh
```

### Configure Storage Paths

**Important**: Update these paths to your own storage locations!

1. **In `FindDatasetToRun.py`** (line 13):
   1. Output dir - 
        ```python
        EOS_OUPUT_DIR = "/eos/user/X/YOURUSER/HCAL/MyHcalAnlzr_Nano"
        ```
   2. The file location of input files are hard coded for now. Change them to desired locations. 
 
        For local_path - Line 433 - ```path = "/eos/cms/store/group/dpg_hcal/comm_hcal/AbortGapData_HighPURun_MD3_2025/"``` 

        For reading from DAS - Line 439 ```path = "/eos/cms/tier0/store/data/Run2023C/TestEnablesEcalHcal/*/*/*"```
    3.  ```whitelist_file``` - run on specific files, if empty it runs on all the files in the directory provided. 
    4.  ```blacklist_file``` - remove blacklisted files.
    5.  ```TOTAL_EVENTS``` - Total events per file to be used to create the HCAL Nano, ```-1``` to run over the full root file

2. **In `digi_fromNano.cc`** (line 25):
   ```cpp
   const string outdir = "/eos/user/X/YOURUSER/HCAL/macro_nano_output/";
   ```

3. **In `digi_process.py`** (line 11):
   ```python
   input_dir = "/eos/user/X/YOURUSER/HCAL/macro_nano_output/"
   ```

4. Create EOS directories in the ```makePlots.sh```:
   ```bash
   eos mkdir -p /eos/user/X/YOURUSER/HCAL/MyHcalAnlzr_Nano
   eos mkdir -p /eos/user/X/YOURUSER/HCAL/macro_nano_output
   ```

---

## Detailed Usage

### FindDatasetToRun.py Options

```
python3 FindDatasetToRun.py [OPTIONS]

Required:
  -d, --date DATE           Date in format DD.MM (e.g., 04.22)
  -r, --run RUN             Whitelist specific run(s)
  -m, --mode MODE           Mode: WholeRun or WholeFill, if not provided than runs single File mode

Optional:
  --local_path              Use local path instead of EOS for input
  --submit_jobs             Submit Condor jobs (WholeRun mode), for the wholeFill currently runs them locally.
  --run_locally             Run jobs locally (WholeRun mode) for debugging purposes
  --check_nano_files        Verify NanoAOD files created
  --make_small              Reduce NanoAOD file size to do it locally, already included in the HcalNano_Template_condor.sh when submit_jobs is used.
  --after_nano              Process digi_process.py after nano creation, also includded in the submit_jobs. But if want to use separately, then submits condor jobs using macro_nano_condor.sh
  --do_digi_process         Run digi_process.py to create the SaveFile.txt. It is advised to run it locally so that the SaveFile.txt does not overwrites when multiple jobs are writing the file. 
  --make_plots              Generate plots using Plotting.py
  --dry                     Dry run (don't submit jobs)
```

## Output Files

### 1. Per-LS ROOT Files (EOS)
**Location**: `/eos/user/X/YOURUSER/HCAL/macro_nano_output/`

**Naming**: `hist_CalibOutput_Run<run>_LS<LS>_<UUID>.root`

**Contents**:
- `hist_<run>_subdet<det>_ieta<η>_iphi<φ>_depth<d>_<entry>_FC`: fC pedestal histogram
- `hist_<run>_subdet<det>_ieta<η>_iphi<φ>_depth<d>_<entry>_ADC`: ADC pedestal histogram
- `ADCvsFC`: 2D histogram of ADC vs fC correlation
- `adc2fc`, `fc2adc`: Conversion graphs

### 2. Summary ROOT Files
**Location**: Current working directory

**Naming**: `hist_CalibOutputSummary_run<run>_LS<LS>_<UUID>.root`

**Contents**:
- Aggregated pedestal statistics per detector subsection
- Mean and RMS distributions

### 3. Text Output 
**Location**: Current working directory. This is the file which is used for saving the values that will be used for making the pedestal plots. The values are appended to this file. **Remember** to delete all the lines in the file when trying to debug and running the ```digi_process.py```.

**Naming**: `SaveFile_<run>.txt`

**Format**:
```
RUN LUMI DAYSINCE FLOATDAY TRENDNAME STAT VALUE
397962 563 123 <UUID> HB_sipmSmall_FC MeanMean 45.2
397962 563 123 <UUID> HB_sipmSmall_FC MeanRMS 1.3
...
```


## Storage Information

### Cleaning Up

```bash
# Remove old per-LS files (keep summaries)
eos rm /eos/user/X/YOURUSER/HCAL/macro_nano_output/hist_CalibOutput_Run*.root

# Archive old runs
tar -czf run_397962_archive.tar.gz WholeRunOutput_397962/
rm -rf WholeRunOutput_397962/

# Check EOS quota
eos quota /eos/user/X/YOURUSER/
```

---


