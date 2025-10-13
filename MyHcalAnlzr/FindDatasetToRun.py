import os, sys
import glob
import time
import json
import ROOT
import argparse

# The global run setup is not tested yet. The local path is working with the run files stored in eos with path + /Run{run}/* format
# The global setup can be check in the FindDataesetToRun_old.py script

EOS_OUPUT_DIR = "/eos/user/n/nparmar/HCAL/MyHcalAnlzr_Nano"

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Process HCAL dataset files.")
    parser.add_argument("-d", "--date", required=True, help="Date in format DD.MM")
    parser.add_argument("-r", "--run", dest="whitelistrun", help="Whitelist run(s), space separated", default="")
    parser.add_argument("-m", "--mode", choices=["WholeRun", "WholeFill", ""], help="Mode: WholeRun or WholeFill", default="")
    parser.add_argument("--local_path", help="Use local path instead of eos", action="store_true", default=False)
    
    args = parser.parse_args()
    
    return args

def get_files_from_local_path(path, runs, blacklist_file):
    """Discover files in a local path."""
    for run in runs:
      allfiles_list = [f for f in glob.glob(path+f"Run{run}/*") if f.endswith(".root") and f.split("/")[-1] not in blacklist_file]
    print("There are",len(allfiles_list),"files total")
    return allfiles_list

def get_files_by_date(path, blacklist_file):
    """Discover files and organize them by date."""
    allfiles_list = [f for f in glob.glob(path+"/*/*/*/*") if f.endswith(".root") and f.split("/")[-1] not in blacklist_file]
    print("There are",len(allfiles_list),"files total")
    
    allfiles_done = []
    if os.path.isfile('allFilesByDate.json'):
        with open('allFilesByDate.json') as jfile:
            allfiles_date = json.load(jfile)
        with open('allRunsByDate.json') as jfile:
            allruns_date = json.load(jfile)
        for dm in allfiles_date:
            allfiles_done += allfiles_date[dm]
    else:
        allfiles_date = {}
        allruns_date = {}
    
    for f in allfiles_list:
        if f in allfiles_done: 
            continue
        run = f.split("/")[11]+f.split("/")[12]
        ftime = os.path.getmtime(f)
        fdate = time.gmtime(ftime)
        fday = fdate[2]
        fmonth = fdate[1]
        dm = str(fday)+"."+str(fmonth)
        if dm not in allfiles_date:
            allfiles_date[dm] = []
            allruns_date[dm] = []
        allfiles_date[dm].append(f)
        if run not in allruns_date[dm]: 
            allruns_date[dm].append(run)
    
    # Save file dict
    with open('allFilesByDate.json', 'w') as jfile:
        json.dump(allfiles_date, jfile)
    with open('allRunsByDate.json', 'w') as jfile:
        json.dump(allruns_date, jfile)
    
    return allruns_date

def select_runs(allruns_date, day, month, whitelistrun):
    """Select runs based on date and whitelist criteria."""
    date_key = day + "." + month
    if date_key not in allruns_date:
        print(f"There are no available runs for this day ({date_key})!")
        return []
    
    pureRuns = []  # Run lasted only during that day
    mixedRuns = []  # Run started on previous day or ended on next day
    
    for run in allruns_date[date_key]:
        mixed = False
        for dm in allruns_date:
            if run in allruns_date[dm] and dm != date_key:
                mixed = True
                break
        if mixed:
            mixedRuns.append(run)
        else:
            pureRuns.append(run)
    
    # Consider using mixed runs only when there are no pure runs
    if any(w in pureRuns for w in whitelistrun) or any(w in mixedRuns for w in whitelistrun):
        print("Using given run")
        runs = [w for w in whitelistrun if w in pureRuns or w in mixedRuns]
    elif pureRuns != []:
        print("Using run from given day")
        runs = pureRuns
    elif mixedRuns != []:
        print("Using run from given day (overlapping with previous or next day)")
        runs = mixedRuns
    else:
        print("There are no available runs for this day!")
        return []
    
    return runs

def get_files_for_runs(runs, path):
    """Get all files related to selected runs."""
    files = []
    for run in runs:
        runstr = run[:3]+"/"+run[3:]
        files += [f for f in glob.glob(path+"/"+runstr+"/*/*") if f.endswith(".root")]
    return files

def select_file_for_processing(files, whitelist_file, WholeRun, WholeFill):
    """Select the appropriate file for processing."""
    myfile = ""
    largefiles = {}
    
    if any([fstr in f for fstr in whitelist_file for f in files]) and not (WholeRun or WholeFill): 
        myfile = [f for fstr in whitelist_file for f in files if fstr in f][0]
    else:
        # Get all large files, sort by time, then process the median file
        for f in files:
            fs = os.path.getsize(f)
            if fs > 3758096384:  # 3.5G
                largefiles[os.path.getmtime(f)] = f
        if largefiles != {}:
            myfile = largefiles[sorted(list(largefiles.keys()))[int(len(largefiles)/2.0)]]
    
    return myfile, largefiles

def process_single_run(myfile, run, date):
    """Process a single run."""
    os.system("cp HcalNano_Template.sh HcalNano_"+run+".sh")
    filein = myfile.replace("/eos/cms/tier0", "").replace("/", "\/")
    os.system('sed -i "s/FILEIN/'+filein+'/g" HcalNano_'+run+'.sh')
    os.system('sed -i "s/XXXXXX/'+run+'/g" HcalNano_'+run+'.sh')
    os.system('sed -i "s/DAY/'+date+'/g" HcalNano_'+run+'.sh')
    os.system('. ./HcalNano_'+run+'.sh')

def process_whole_run(largefiles, run, islocal_path=False):
    """Process all files in a run."""
    files = [largefiles[f] for f in largefiles]
    os.system("mkdir -p WholeRunOutput_"+run)
    print(f"DEBUG: Creating directory WholeRunOutput_{run}")
    
    for myfile in files:
      fname = myfile.split("/")[-1].split(".")[0]
      print(f"DEBUG: Processing file {myfile}, fname is {fname}")
      os.system("cp HcalNano_Template.sh HcalNano_"+run+"_"+fname+".sh")
      print(f"DEBUG: Copied HcalNano_Template.sh to HcalNano_{run}_{fname}.sh")
      
      if islocal_path:
          filein = ("file:"+myfile).replace("/", "\/")
      else:
        filein = myfile.replace("/eos/cms/tier0", "").replace("/", "\/")
      print(f"DEBUG: filein for sed is {filein}")
      
      os.system('sed -i "s/FILEIN/'+filein+'/g" HcalNano_'+run+'_'+fname+'.sh')
      print(f"DEBUG: Replaced FILEIN in HcalNano_{run}_{fname}.sh")
      
      os.system('sed -i "s/XXXXXX/'+run+'_'+fname+'/g" HcalNano_'+run+'_'+fname+'.sh')
      print(f"DEBUG: Replaced XXXXXX in HcalNano_{run}_{fname}.sh")
      
      os.system('sed -i "s/_DAY//g" HcalNano_'+run+'_'+fname+'.sh')
      print(f"DEBUG: Removed _DAY in HcalNano_{run}_{fname}.sh")
      
      os.system('sed -i "s/-n 5000/-n 300/g" HcalNano_'+run+"_"+fname+'.sh')
      print(f"DEBUG: Changed -n 5000 to -n 300 in HcalNano_{run}_{fname}.sh")
      
     

      os.system('. ./HcalNano_'+run+'_'+fname+'.sh '+ EOS_OUPUT_DIR)
      print(f"DEBUG: Executed HcalNano_{run}_{fname}.sh with output dir {EOS_OUPUT_DIR}")

      sys.exit()
      os.system('./macro_nano '+fname+' 1')
      print(f"DEBUG: Ran ./macro_nano {fname} 1")
      os.system('python3 digi_process.py '+run+' WholeRun '+fname)
      print(f"DEBUG: Ran python3 digi_process.py {run} WholeRun {fname}")
      os.system('mv *'+fname+'* WholeRunOutput_'+run)
      print(f"DEBUG: Moved files matching *{fname}* to WholeRunOutput_{run}")

def process_whole_fill(largefiles, run, WholeFill, date):
    """Process all files in a fill."""
    files = [largefiles[f] for f in largefiles]
    os.system("mkdir -p WholeFillOutput_"+WholeFill)
    tohadd = []
    nentries = []
    
    for myfile in files:
        fname = myfile.split("/")[-1].split(".")[0]
        os.system("cp HcalNano_Template.sh HcalNano_"+run+"_"+fname+".sh")
        filein = myfile.replace("/eos/cms/tier0", "").replace("/", "\/")
        os.system('sed -i "s/FILEIN/'+filein+'/g" HcalNano_'+run+'_'+fname+'.sh')
        os.system('sed -i "s/XXXXXX/'+run+'_'+fname+'/g" HcalNano_'+run+'_'+fname+'.sh')
        os.system('sed -i "s/_DAY//g" HcalNano_'+run+'_'+fname+'.sh')
        os.system('sed -i "s/-n 5000/-n 500/g" HcalNano_'+run+"_"+fname+'.sh')
        
        tohadd.append(f'{EOS_OUPUT_DIR}/output_CalibRuns_Nano_Run'+run+'_'+fname+'_temp.root')
        fin = ROOT.TFile.Open(tohadd[-1], "READ")
        tree = fin.Get("Events")
        nentries.append(str(tree.GetEntries()))
        fin.Close()
        os.system('mv *'+fname+'* WholeFillOutput_'+WholeFill)
    
    print('./macro_nano '+date+' '+WholeFill+' '+' '.join(nentries))
    os.system('./macro_nano '+date+' '+WholeFill+' '+' '.join(nentries))
    os.system('mv *Fill'+WholeFill+'* WholeFillOutput_'+WholeFill)

def main():
    
    # Configuration
    blacklist_file = ["244aa98d-1bc6-4c3f-bf02-36032473b104.root"]
    whitelist_file = ["3c982479-12d1-407c-8399-67b38c82f709.root"]
    
    args = parse_arguments()
    # Parse date
    date = args.date
    day = str(int(date.split(".")[0]))
    month = str(int(date.split(".")[1]))
    
    # Parse whitelist runs
    whitelistrun = args.whitelistrun.split(" ") if args.whitelistrun else []
    
    # Parse mode
    if args.mode == "WholeRun":
        WholeRun, WholeFill = True, False
    elif args.mode:
        WholeRun, WholeFill = False, args.mode
    else:
        WholeRun, WholeFill = False, False
    print("run(s):", whitelistrun, "mode:", args.mode)
    # Set path
    if args.local_path:
        print("Using local path ... which is hardcoded for now in the script")
        path = "/eos/cms/store/group/dpg_hcal/comm_hcal/AbortGapData_HighPURun_MD3_2025/"
        runs = whitelistrun
        files = get_files_from_local_path(path, runs, blacklist_file)
        
    else:
        print("Using tier0 path ... which is hardcoded for now in the script")
        path = "/eos/cms/tier0/store/data/Run2023C/TestEnablesEcalHcal/*/*/*"

        # Get files organized by date
        allruns_date = get_files_by_date(path, blacklist_file)
        
        # Select run
        runs = select_runs(allruns_date, day, month, whitelistrun)
        if not runs:
            exit()
        
        # Get files for selected runs
        files = get_files_for_runs(runs, path)
    
    # print("DEBUG: There are",len(files),"files for the selected runs and the files are - ",files)
    
    # Select file for processing
    myfile, largefiles = select_file_for_processing(files, whitelist_file, WholeRun, WholeFill)
    
    if myfile == "":
        print("NO FILES FOUND!")
        exit()
    else:
        print("Processing", myfile, "...")
    print(f"DEBUG: myfile is {myfile} and largefiles are {largefiles}")
    print(f"DEBUG: len(largefiles) is {len(largefiles)} myfile is {myfile} in largefiles.values() is {myfile in largefiles.values()} keys for myfile is {[k for k,v in largefiles.items() if v==myfile]}")
    print(f"DEBUG: files len is {len(files)}")
    print(f"DEBUG: file that is in files but not in largefiles is {[f for f in files if f not in largefiles.values()]}")

    if args.local_path:
        run = runs[0]
    else:
      run = myfile.split("/")[11]+myfile.split("/")[12]

    print(f"DEBUG: run is {run}")

    # Process based on mode
    if not (WholeRun or WholeFill):
        process_single_run(myfile, run, date)
    elif WholeRun:
        process_whole_run(largefiles, run, islocal_path=args.local_path)
    else:  # WholeFill
        process_whole_fill(largefiles, run, WholeFill, date)
    
    print("Done making NanoTuple!")

if __name__ == "__main__":
    main()
