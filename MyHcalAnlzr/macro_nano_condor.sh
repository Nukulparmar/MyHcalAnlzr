#!/bin/bash
# This is a template script for condor job submission to run macro_nano and digi_process.py
# It doesnot work with cmsenv directly, need to give a CMSSW env as input
IFS=';' read -r -a args <<< "$1"
currentDir=${args[0]}
fname=${args[1]}
outputEosPath=${args[2]}
run=${args[3]}
CMSSWVersion=${args[4]}

source /cvmfs/cms.cern.ch/cmsset_default.sh
scram p ${CMSSWVersion}
cd ${CMSSWVersion}/src
cmsenv
cd -

echo "Current Directory: $currentDir"
echo "fname: $fname"
echo "Output EOS Path: $outputEosPath"
echo "Run: $run"
echo "CMSSW Version: $CMSSWVersion"

echo "current directory before changing: $(pwd)"
cd $currentDir
echo "Changed to directory: $(pwd)"
cmsenv
ls -lrth

echo "Running macro_nano with input file: $fname"
./macro_nano ${fname} 1
# echo "running digi_process.py with run: $run and input file: $fname" # not a good idea to run digi_process.py in condor as it might overright on the savefile when files from multiple jobs are merged
# python3 digi_process.py ${run} WholeRun ${fname}

