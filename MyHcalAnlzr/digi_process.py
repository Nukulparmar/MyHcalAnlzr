import ROOT
import os, sys
import re
from array import array

##### Start
ROOT.gStyle.SetOptFit(1)
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)

input_dir = "/eos/user/n/nparmar/HCAL/macro_nano_output/"

# Command line arguments
days = sys.argv[1]
lumi = sys.argv[2]
floatday = sys.argv[3] # e.g. "05.07" or UUID for per-LS files
WholeRun = True if lumi=="WholeRun" else False

# Find all files matching the pattern (handle multiple LS files)
if not WholeRun:
  # Normal mode: Find files with pattern ending with floatday
  all_files = [f for f in os.listdir(input_dir) if f.startswith("hist_CalibOutput_") and f.endswith("_"+floatday+".root")]
  if not all_files:
    print("ERROR: No files found matching pattern *_"+floatday+".root")
    sys.exit(1)
  # Extract run ID from first file
  runid = all_files[0].split("_")[2]  # Gets run number from filename
  print(f"Found {len(all_files)} file(s) for run {runid}")
else:
  # WholeRun mode: days is run number, floatday is the UUID/identifier
  runid = days
  # Find all files matching: hist_CalibOutput_Run<runid>_LS*_<floatday>.root
  pattern = f"hist_CalibOutput_Run{runid}_LS"
  all_files = [f for f in os.listdir(input_dir) if f.startswith(pattern) and f.endswith("_"+floatday+".root")]
  if not all_files:
    print(f"ERROR: No files found matching pattern {pattern}*_{floatday}.root")
    sys.exit(1)
  print(f"Found {len(all_files)} file(s) for run {runid} in WholeRun mode")

# Sort files by LS number
all_files.sort(key=lambda x: int(re.search(r'LS(\d+)_', x).group(1)) if re.search(r'LS(\d+)_', x) else 0)
print(f"Processing files in order: {all_files}")

# Process each file
for fileIdx, fileName in enumerate(all_files):
  fileName = input_dir + fileName
  print(f"\n{'='*60}")
  print(f"Processing file {fileIdx+1}/{len(all_files)}: {fileName}")
  print(f"{'='*60}")
  
  # Extract LS from filename
  ls_match = re.search(r'LS(\d+)_', fileName)
  if ls_match:
    lumi = ls_match.group(1)
  else:
    print(f"WARNING: Could not extract LS from filename {fileName}, skipping")
    continue
  
  fin=ROOT.TFile.Open(fileName, "READ")
  if not fin or fin.IsZombie():
    print(f"ERROR: Could not open file {fileName}")
    continue
    
  histos = {}
  histos["FC"] = {}
  histos["ADC"] = {}
  finalhistos = {}
  subdets = ["HB", "HE", "HF", "HO"]
  for subdet in subdets:
    histos["FC"][subdet] = {}
    histos["ADC"][subdet] = {}

  # Load
  hist_count = 0
  for key in fin.GetListOfKeys():
    hname = key.GetName()
    if "_ADC" in hname:
      histos["ADC"][hname[hname.find("subdet")+6:hname.find("subdet")+8]][hname] = fin.Get(hname)
      hist_count += 1
    elif "_FC" in hname:
      histos["FC"][hname[hname.find("subdet")+6:hname.find("subdet")+8]][hname] = fin.Get(hname)
      hist_count += 1
  print(f"Loaded {hist_count} histograms from {fileName}")

  # Define everything to process
  pedtrend = ["HB_sipmSmall", "HB_sipmLarge", "HE_sipmSmall", "HE_sipmLarge", "HF", "HO"]
  for depth in range(4):
    pedtrend.append("HB_depth"+str(depth+1))
  for depth in range(7):
    pedtrend.append("HE_depth"+str(depth+1))
  pedtrend += ["HB_sipmSmall_phi,1,72", "HB_sipmLarge_phi,1,72", "HE_sipmSmall_phi,1,72", "HE_sipmLarge_phi,1,72"]
  pedtrend += ["HB_sipmSmall_phi,18,19", "HB_sipmLarge_phi,18,19", "HE_sipmSmall_phi,18,19", "HE_sipmLarge_phi,18,19"]
  pedtrend += ["HB_sipmSmall_phi,36,37", "HB_sipmLarge_phi,36,37", "HE_sipmSmall_phi,36,37", "HE_sipmLarge_phi,36,37"]
  pedtrend += ["HB_sipmSmall_HBP14RM1", "HB_sipmLarge_HBP14RM1", "HB_sipmSmall_HBM09RM3", "HB_sipmLarge_HBM09RM3"]

  def IsHBP14RM1(hname):
    if "iphi51" in hname and "ieta-" not in hname: return True
    return False
  def IsHBM09RM3(hname):
    if "iphi32" in hname and "ieta-" in hname: return True
    return False

  # Process
  for p in pedtrend:
    subdet = p.split("_")[0]
    finalhistos[p+"_ADC_Mean"] = ROOT.TH1F(p+"_pedADCMean_run"+runid+"_LS"+lumi, "Pedestal Mean; ADC; Entries", 960, 0, 32)
    finalhistos[p+"_ADC_RMS"] = ROOT.TH1F(p+"_pedADCRMS_run"+runid+"_LS"+lumi, "Pedestal RMS; ADC; Entries", 960, 0, 32)
    finalhistos[p+"_FC_Mean"] = ROOT.TH1F(p+"_pedFCMean_run"+runid+"_LS"+lumi, "Pedestal Mean; fC; Entries", 10000, 0, 1000)
    finalhistos[p+"_FC_RMS"] = ROOT.TH1F(p+"_pedFCRMS_run"+runid+"_LS"+lumi, "Pedestal RMS; fC; Entries", 10000, 0, 1000)
    for unit in ["ADC", "FC"]:
      for hname in histos[unit][subdet]:
        skip = False
        for cut in p.split("_")[1:]:
          if "phi" in cut: # Special phi cuts
            if all("phi"+phicut+"_" not in hname for phicut in cut.split(",")[1:]): skip = True
          elif "HBP14RM" in cut:
            if not IsHBP14RM1(hname): skip=True
          elif "HBM09RM" in cut:
            if not IsHBM09RM3(hname): skip=True
          elif cut not in hname: skip = True
        if ("HB" in p) and ("HBP14RM1" not in p) and (IsHBP14RM1(hname)): skip=True
        if ("HB" in p) and ("HBM09RM3" not in p) and (IsHBM09RM3(hname)): skip=True
        if not skip:
          mean = histos[unit][subdet][hname].GetMean()
          rms = histos[unit][subdet][hname].GetRMS()
          if mean!=0.0 and rms!=0.0:
            finalhistos[p+"_"+unit+"_Mean"].Fill(mean)
            finalhistos[p+"_"+unit+"_RMS"].Fill(rms)

  # Write in text file
  savefilename = "SaveFile_"+runid+".txt"
  with open(savefilename, "a") as file:
    # To be written:
    # RUN LUMI DAYSINCE FLOATDAY TRENDNAME MeanMean/MeanRMS/RMSMean value
    idname = runid+" "+lumi+" "+days+" "+floatday if not WholeRun else runid+" "+lumi+" X X"
    entries_written = 0
    for trend in finalhistos:
      if trend.endswith("RMS"): continue
      if finalhistos[trend].GetMean()==0: continue # HO in Full runs is empty
      trend = trend[:-5]
      file.write(idname+" "+trend+" MeanMean "+str(finalhistos[trend+"_Mean"].GetMean()) + "\n")
      file.write(idname+" "+trend+" MeanRMS "+str(finalhistos[trend+"_RMS"].GetMean()) + "\n")
      file.write(idname+" "+trend+" RMSMean "+str(finalhistos[trend+"_Mean"].GetRMS()) + "\n")
      file.write(idname+" "+trend+" RMSRMS "+str(finalhistos[trend+"_RMS"].GetRMS()) + "\n")
      entries_written += 4
  print(f"Wrote {entries_written} lines to {savefilename}")

  # Write histograms (per LS)
  # rootfilename = "hist_CalibOutputSummary_run"+runid+"_LS"+lumi+"_"+floatday+".root"
  # fout=ROOT.TFile.Open(rootfilename, "RECREATE")
  # if not fout or fout.IsZombie():
  #   print(f"ERROR: Could not create output file {rootfilename}")
  #   fin.Close()
  #   continue
  
  # hists_written = 0
  # for fhist in finalhistos:
  #   finalhistos[fhist].Write()
  #   hists_written += 1
  # fout.Close()
  # fin.Close()
  # print(f"Wrote {hists_written} histograms to {rootfilename}")

print(f"\n{'='*60}")
print(f"Done! Processed {len(all_files)} LS files.")
print(f"All results appended to SaveFile_{runid}.txt")
print(f"{'='*60}")
exit()