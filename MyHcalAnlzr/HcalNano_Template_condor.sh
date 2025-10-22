#!/bin/bash
# Parse semi-colon separated arguments
IFS=';' read -r -a args <<< "$1"
CMSSWVersion=${args[0]}
inputFile=${args[1]}
outputFile=${args[2]}
outputEosPath=${args[3]}
totalEvents=${args[4]}
run=${args[5]}
fname=${args[6]}
homedir=${args[7]}

echo "CMSSWVersion: ${CMSSWVersion}"
echo "inputFile: ${inputFile}"
echo "outputFile: file:${outputEosPath}/output_CalibRuns_Nano_Run${run}_${fname}.root"
echo "outputEosPath: ${outputEosPath}"
echo "totalEvents: ${totalEvents}"
echo "run: ${run}"
echo "file: ${fname}"

source /cvmfs/cms.cern.ch/cmsset_default.sh
scram p ${CMSSWVersion}
cd ${CMSSWVersion}/src
cmsenv
cd -

eos_out_file=${outputEosPath}/output_CalibRuns_Nano_Run${run}_${fname}.root
echo "Output EOS file will be: ${eos_out_file}"

ls -lthr
echo "Running the command"
echo "cmsDriver.py NANO \
    -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask \
    --processName=PFG \
    --datatier NANOAOD \
    --eventcontent NANOAOD \
    --filein ${inputFile} \
    --fileout file:${eos_out_file} \
    -n ${totalEvents} \
    --nThreads 4 \
    --conditions auto:run3_data_prompt \
    --era Run3 \
    --python_filename cmsdriver_${run}_${fname}.py \
    --no_exec \
    --customise DPGAnalysis/HcalNanoAOD/customiseHcalCalib_cff.customiseHcalCalib
cmsRun cmsdriver_${run}_${fname}.py
"

time cmsDriver.py NANO \
    -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask \
    --processName=PFG \
    --datatier NANOAOD \
    --eventcontent NANOAOD \
    --filein ${inputFile} \
    --fileout file:${eos_out_file} \
    -n ${totalEvents} \
    --nThreads 4 \
    --conditions auto:run3_data_prompt \
    --era Run3 \
    --python_filename cmsdriver_${run}_${fname}.py \
    --no_exec \
    --customise DPGAnalysis/HcalNanoAOD/customiseHcalCalib_cff.customiseHcalCalib
cmsRun cmsdriver_${run}_${fname}.py
echo "Skipping cmsDriver and cmsRun for testing purposes"
echo "Finished processing run ${run}, file ${fname}"
echo "making output smaller by removing some branches"
echo "current directory before changing: $(pwd)"
ls -lrth
cd $homedir
echo "Changed to directory: $(pwd)"
cmsenv
ls -lrth

# echo "running MakeSmall.py"
# time python3 MakeSmall.py ${eos_out_file} --debug

# echo "Running macro_nano with input file: $fname"
# time ./macro_nano ${fname} 1
echo "running digi_process.py with run: $run and input file: $fname"
time python3 digi_process.py ${run} WholeRun ${fname}

ls -lrth

echo "All done for run ${run}, file ${fname}"