import os, sys
import subprocess
import glob
import time
import json
import ROOT
import argparse

# The global run setup is not tested yet. The local path is working with the run files stored in eos with path + /Run{run}/* format
# The global setup can be check in the FindDataesetToRun_old.py script

EOS_OUPUT_DIR = "/eos/user/n/nparmar/HCAL/MyHcalAnlzr_Nano" # The output directory for the nano tuples
JOB_SCRIPT = "HcalNano_Template_condor.sh"  # The script to run for condor jobs
CMSSW_VERSION= "CMSSW_15_0_6"
# TMP_PATH = "/tmp/nparmar/"  
TOTAL_EVENTS = -1  # Total events to process per job in condor submission
ifDebug = True  # If True, print debug information # TODO : print only when needed

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Process HCAL dataset files.")
    parser.add_argument("-d", "--date", required=True, help="Date in format DD.MM")
    parser.add_argument("-r", "--run", dest="whitelistrun", help="Whitelist run(s), space separated", default="")
    parser.add_argument("-m", "--mode", choices=["WholeRun", "WholeFill", ""], help="Mode: WholeRun or WholeFill", default="")
    parser.add_argument("--local_path", help="Use local path instead of eos", action="store_true", default=False)
    parser.add_argument("--submit_jobs", help="Submit jobs to condor (only for WholeRun mode)", action="store_true", default=False)
    parser.add_argument("--check_nano_files", help="Check if the nano files are created successfully (only for WholeRun mode)", action="store_true", default=False)
    parser.add_argument("--run_locally", help="Run the jobs locally instead of condor (only for WholeRun mode)", action="store_true", default=False)
    parser.add_argument("--after_nano", help="Run digi_process.py after making all nano tuples (only for WholeRun mode)", action="store_true", default=False)
    parser.add_argument("--dry", help="Dry run for condor submission (only for WholeRun mode)", action="store_true", default=False)
    parser.add_argument("--make_small", help="Make the input file smaller by removing unnecessary branches and events", action="store_true", default=False)
    parser.add_argument("--do_digi_process", help="Run digi_process.py script after making nano tuples", action="store_true", default=False)
    args = parser.parse_args()
    # Ensure submit_jobs and after_nano are not both True
    if args.submit_jobs and args.run_locally:
        print("Error: --submit_jobs and --run_locally cannot be used together.")
        sys.exit(1)
    return args

def MakeSmall(path):
    patht1 = path.replace(".root", "_temp.root")
    patht2 = path.replace(".root", "_temp2.root")
    print(f"path: {path}, patht1: {patht1}, patht2: {patht2}")
    
    try:
        tries = 0
        while tries < 10:
            # Remove HLT branches and filter non-eventtype 1 events
            #os.system('rooteventselector -s "(uMNio_EventType == 1)" -e "HLT_*" '+path+':Events '+patht1)
            print("running rooteventselector ...")
            os.system('rooteventselector -s "(uMNio_EventType == 1)" -e "HLT*,*RecHit*,DigiHF_ok*,DigiHO_er*,DigiHO_dv*,*Error,*fiber*,*flags,*pedestalfc*,*subdet,*soi,*tdc*,*valid" '+path+':Events '+patht1)
            # Re-compress
            print("running haddnano ...")
            success = os.system('python3 haddnano.py '+patht2+' '+patht1)
            print(f"Success: {success}")
            os.system('rm '+patht1)
            if success==0:
                break
            else:
                os.system('rm '+patht2)
            tries += 1
    except OSError: # File not found
        exit()
    except KeyboardInterrupt:
        exit()
    
    os.system('mv '+path+' '+path.replace(".root", "_FULL.root"))
    os.system('mv '+patht2+' '+path)
    print(f"Finished making file smaller: {path}")
    
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
    print(f"DEBUG: whitelist_file is {whitelist_file}")
    if any([fstr in f for fstr in whitelist_file for f in files]) and not (WholeRun or WholeFill): 
        myfile = [f for fstr in whitelist_file for f in files if fstr in f][0]
        
    else:
        # Get all large files, sort by time, then process the median file
        for f in files:
            # if whitelist_file and not any([fstr in f for fstr in whitelist_file]): # Skip if not in whitelist
            #     continue
            fs = os.path.getsize(f)
            # if fs > 3758096384:  # 3.5G
            if fs > 1000000000:  # 1G
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


def submit_condor_job(job_content, job_script, jdl_file_name, isdry=False):
    """Submit jobs to condor for processing HCAL nano ntuples using JOB_SCRIPT. 
       arguments: inputfiles (list of input files), run (run number), cmssw_version (CMSSW version to use),
                  total_events (total number of events to process per job), isdry (if True, does not submit jobs)
    """
    
    condor_jdl_file = jdl_file_name
    with open(condor_jdl_file, "w") as f:
        f.write("universe = vanilla\n")
        # f.write("+JobFlavour = espresso\n")
        f.write(f"executable = {job_script}\n")
        f.write("request_cpus = 4\n")
        # f.write("request_memory = 4 GB\n")
        # # f.write("request_disk = 2 GB\n")
        f.write("+MaxRuntime = 40000\n")
        f.write("should_transfer_files = YES\n")
        f.write("when_to_transfer_output = ON_EXIT\n")
        f.write("Arguments = $(args)\n")
        f.write("output = $(out)\n")
        f.write("error = $(err)\n")
        f.write("log = $(log)\n")
        f.write("\nqueue args, out, err, log from (\n")

        for job in job_content:
            f.write(job)

        f.write(")\n")
    
    print(f"Condor submission file created {condor_jdl_file} with {len(job_content)} jobs.")

    #Submit jobs 
    try:
        if not isdry:
            os.system(f"condor_submit {condor_jdl_file}")
            
        else:
            print(f"Dry run: condor_submit {condor_jdl_file} (not actually submitted)")
    except Exception as e:
        print(f"Error submitting condor jobs: {e}")

def check_nano_files(largefiles,run):
    """Check if the nano files are created successfully."""
    files = [largefiles[f] for f in largefiles]
    for input_file in files:
        input_file_name = input_file.split("/")[-1].split(".root")[0]
        nano_file = f"{EOS_OUPUT_DIR}/output_CalibRuns_Nano_Run{run}_{input_file_name}.root"
        if not os.path.isfile(nano_file):
            print(f"Nano file {nano_file} not found!")
        else:
            print(f"Nano file {nano_file} exists.")


def process_whole_run(largefiles, run, islocal_path=False, submit_jobs=False, isdry=False, run_locally=False):
    """Process all files in a run."""

    files = [largefiles[f] for f in largefiles]
    os.system("mkdir -p WholeRunOutput_"+run)
    print(f"DEBUG: Creating directory WholeRunOutput_{run}")
    
    if submit_jobs:
        print(f"DEBUG: Submitting condor jobs for run {run}")
        condor_out = "condor_out_"+run
        os.makedirs(condor_out, exist_ok=True)
        jdl_file_name = f"condor_{run}_more_cpus.jdl"
        homedir = os.getcwd()
        job_content = []
        for i, file in enumerate(files):
            fname = file.split("/")[-1].split(".")[0]
            if file.startswith("/eos/cms/tier0"):
                xrootd_path = f"root://xrootd-cms.infn.it{file}"
            elif file.startswith("/eos/cms/store/group/dpg_hcal"):
                # xrootd_path = f"root://eosuser.cern.ch{input_file}"
                xrootd_path = f"file:{file}"
            else:
                xrootd_path = input_file
            outfile = f"condor_out_{run}/output_{run}_{fname}.stdout"
            errfile = f"condor_out_{run}/error_{run}_{fname}.stderr"
            logfile = f"condor_out_{run}/log_{run}_{fname}.log"
            args = f"{CMSSW_VERSION};{xrootd_path};{file};{EOS_OUPUT_DIR};{TOTAL_EVENTS};{run};{fname};{homedir}"
            line_end = "," if i < len(files)-1 else ""
            job_content.append(f'"{args}", {outfile}, {errfile}, {logfile}{line_end}\n')
            # break # For testing, process only one file. Remove this line for full processing.
        submit_condor_job(job_content, job_script=JOB_SCRIPT, jdl_file_name=jdl_file_name, isdry=isdry)
        print(f"Submitted condor jobs for run {run}.")
        sys.exit()
 
    elif run_locally:
        print(f"DEBUG: Running locally for run {run}")
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
            
            os.system('sed -i "s/XXXXXX/'+run+'_'+fname+'_10evt/g" HcalNano_'+run+'_'+fname+'.sh')
            print(f"DEBUG: Replaced XXXXXX in HcalNano_{run}_{fname}.sh")
            
            os.system('sed -i "s/_DAY//g" HcalNano_'+run+'_'+fname+'.sh')
            print(f"DEBUG: Removed _DAY in HcalNano_{run}_{fname}.sh")
            
            os.system('sed -i "s/-n 5000/-n 10/g" HcalNano_'+run+"_"+fname+f'.sh')
            print(f"DEBUG: Changed -n 5000 to -n 10 in HcalNano_{run}_{fname}.sh")
            
            os.system('. ./HcalNano_'+run+'_'+fname+'.sh '+ EOS_OUPUT_DIR)
            print(f"DEBUG: Executed HcalNano_{run}_{fname}.sh with output dir {EOS_OUPUT_DIR}")
            sys.exit()

def process_after_nano_for_WholeRun(largefiles, run, run_locally=False, isdry=False):
    """Process digi_process.py after making all nano tuples."""
        # After making all nano tuples, run the digi_process.py script to make histograms
    
    print(f"DEBUG: Creating directory WholeRunOutput_{run}")
    os.system("mkdir -p WholeRunOutput_"+run)
        
    if run_locally:
        print(f"DEBUG: Running digi_process.py for run {run} after making all nano tuples")
        files = [largefiles[f] for f in largefiles]
        for myfile in files:
            fname = myfile.split("/")[-1].split(".")[0]
            print(f"DEBUG: Processing file {myfile}, fname is {fname}")
            os.system('./macro_nano '+fname+' 1')
            print(f"DEBUG: Ran ./macro_nano {fname} 1")
        sys.exit()
    else:
        print("DEBUG: Running macro nano and digi_process.py for all files in condor jobs")
        submit_job_for_macro_nano(largefiles, run, isdry=isdry)
        print(f"Submitted condor jobs for run {run}.")
        sys.exit()
 
def do_digi_process(files, run):
    """Run digi_process.py script."""
    for myfile in files:
        fname = myfile.split("/")[-1].split(".")[0]
        os.system('python3 digi_process.py '+run+' WholeRun '+fname)
        print(f"DEBUG: Ran python3 digi_process.py {run} WholeRun {fname}")

        os.system(f'mv hist_CalibOutput_hadd_{run}.root hist_CalibOutput_hadd_{run}.root_old')

        os.system(f'hadd -f hist_CalibOutput_hadd_{run}.root hist_CalibOutputSummary_run'+run+'*.root')
        print(f"DEBUG: Merged hist_CalibOutput_hadd_{fname}.root into hist_CalibOutput_hadd_{run}.root")
        
        os.system('mv *'+fname+'* WholeRunOutput_'+run)
        print(f"DEBUG: Moved files matching *{fname}* to WholeRunOutput_{run}")
    os.system(f"bash makePlots.sh {run}")

def create_tarball_current_dir(tar_name="MyHcalAnlzr.tar.gz"):
    """
    Create a tarball of the current directory, excluding condor_out*, WholeRunOuput*, and *.jdl files.
    The tarball is saved in the current directory.
    """
    current_dir = os.getcwd()
    exclude_patterns = [
        "--exclude=condor_out*",
        "--exclude=WholeRunOuput*",
        "--exclude=*.jdl"
    ]
    cmd = [
        "tar", "-czvf", tar_name,
        *exclude_patterns,
        "-C", current_dir, "."
    ]
    subprocess.run(cmd, check=True)
    print(f"Tarball created: {os.path.join(current_dir, tar_name)}")

def submit_job_for_macro_nano(largefiles, run, isdry=False):
    """Make job arguments for macro_nano script."""
    files = [largefiles[f] for f in largefiles]
    jdl_file_name = f"condor_macro_nano_{run}.jdl"
    job_content = []
    current_dir = os.getcwd()
    condor_out_dir = f"condor_out_nano_{run}"
    os.makedirs(condor_out_dir, exist_ok=True)
    for i,myfile in enumerate(files):
        fname = myfile.split("/")[-1].split(".")[0]
        args = f"{current_dir};{fname};{EOS_OUPUT_DIR};{run};{CMSSW_VERSION}"
        outfile = f"{condor_out_dir}/output_macro_nano_{run}_{fname}.stdout"
        errfile = f"{condor_out_dir}/error_macro_nano_{run}_{fname}.stderr"
        logfile = f"{condor_out_dir}/log_macro_nano_{run}_{fname}.log"

        job_content.append(f'"{args}", {outfile}, {errfile}, {logfile}\n')

    submit_condor_job(job_content, job_script="macro_nano_condor.sh", jdl_file_name=jdl_file_name, isdry=isdry)

def skim_nano_files(largefiles,run):
    """Make the input files smaller by removing unnecessary branches and events."""
    files = [largefiles[f] for f in largefiles]
    for myfile in files:
        fname = myfile.split("/")[-1].split(".")[0]
        Nano_file_name = f"{EOS_OUPUT_DIR}/output_CalibRuns_Nano_Run{run}_{fname}.root"
        if not os.path.isfile(Nano_file_name):
            print(f"Nano file {Nano_file_name} not found! Skipping...")
            continue
        MakeSmall(Nano_file_name)
        print(f"Finished making file smaller: {Nano_file_name}")   
        sys.exit()   

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
    # blacklist_file = ["0eea9dfb-dfdf-4ce0-964e-42570267a677.root",
    #                   "]  
    # files_to_run = ["c9732b3e-7ef4-494d-9b11-351000e5c87b.root","62c86a49-10e1-47ef-9567-8265c9a033da.root",
    # "168c68f2-6e19-4849-8a99-626b975ee677.root", "a1ea4f6c-3af8-4637-bf74-2b612a04755c.root", "33329bbe-4765-4485-8a0f-b78da77d1960.root",
    # "08360896-e8a2-4729-ba71-63301a63e0d6.root", "687cbe1b-c456-4c3f-88f4-0d768e2858e4.root"
    # ]
    # whitelist_file = files_to_run


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
    # print(f"DEBUG: myfile is {myfile} and largefiles are {largefiles}")
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
        if args.submit_jobs or args.run_locally:
            print("DEBUG: Processing WholeRun ...")
            process_whole_run(largefiles, run, islocal_path=args.local_path, submit_jobs=args.submit_jobs, isdry=args.dry, run_locally=args.run_locally)
        if args.check_nano_files:
            print("DEBUG: Checking nano file creation ...")
            check_nano_files(largefiles, run)
        if args.make_small:
            print("DEBUG: Making input files smaller ...")
            skim_nano_files(largefiles,run)
        if args.after_nano:
            print("DEBUG: Running digi_process.py after making all nano tuples ...")
            process_after_nano_for_WholeRun(largefiles, run, run_locally=args.run_locally, isdry=args.dry)
        if args.do_digi_process:
            print("DEBUG: Running digi_process.py ...")
            do_digi_process(files, run)
            print("DEBUG: Finished digi_process")
    else:  # WholeFill
        process_whole_fill(largefiles, run, WholeFill, date)
    
    # print(f"Done with the parer!")

if __name__ == "__main__":
    main()
