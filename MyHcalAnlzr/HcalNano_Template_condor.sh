#!/bin/bash
# Parse semi-colon separated arguments
IFS=';' read -r -a args <<< "$1"
CMSSWVersion=${args[0]}
inputFile=${args[1]}
outputFile=${args[2]}
outputEosPath=${args[3]}
totalEvents=${args[4]}
run=${args[5]}
file=${args[6]}

echo "CMSSWVersion: ${CMSSWVersion}"
echo "inputFile: ${inputFile}"
echo "outputFile: file:${outputEosPath}/output_CalibRuns_Nano_Run${outputFile}.root"
echo "outputEosPath: ${outputEosPath}"
echo "totalEvents: ${totalEvents}"
echo "run: ${run}"
echo "file: ${file}"

source /cvmfs/cms.cern.ch/cmsset_default.sh
scram p ${CMSSWVersion}
cd ${CMSSWVersion}/src
cmsenv
cd -

data
ls -lthr
echo "Running the command"
echo "cmsDriver.py NANO \
    -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask \
    --processName=PFG \
    --datatier NANOAOD \
    --eventcontent NANOAOD \
    --filein ${inputFile} \
    --fileout file:${outputEosPath}/output_CalibRuns_Nano_Run${run}_${outputFile}.root \
    -n ${totalEvents} \
    --nThreads 4 \
    --conditions auto:run3_data_prompt \
    --era Run3 \
    --python_filename cmsdriver_${run}_${file}.py \
    --no_exec \
    --customise DPGAnalysis/HcalNanoAOD/customiseHcalCalib_cff.customiseHcalCalib
cmsRun cmsdriver_${run}_${file}.py
"

cmsDriver.py NANO \
    -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask \
    --processName=PFG \
    --datatier NANOAOD \
    --eventcontent NANOAOD \
    --filein ${inputFile} \
    --fileout file:${outputEosPath}/output_CalibRuns_Nano_Run${outputFile}.root \
    -n ${totalEvents} \
    --nThreads 4 \
    --conditions auto:run3_data_prompt \
    --era Run3 \
    --python_filename cmsdriver_${run}_${file}.py \
    --no_exec \
    --customise DPGAnalysis/HcalNanoAOD/customiseHcalCalib_cff.customiseHcalCalib
cmsRun cmsdriver_${run}_${file}.py
