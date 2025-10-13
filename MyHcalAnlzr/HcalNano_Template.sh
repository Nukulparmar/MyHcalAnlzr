ouput_eos_path=$1
cmsDriver.py NANO \
    -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask \
    --processName=PFG \
    --datatier NANOAOD \
    --eventcontent NANOAOD \
    --filein FILEIN \
    --fileout file:${ouput_eos_path}/output_CalibRuns_Nano_RunXXXXXX_DAY.root \
    -n 5000 \
    --nThreads 4 \
    --conditions auto:run3_data_prompt \
    --era Run3 \
    --python_filename cmsdriver_XXXXXX.py \
    --no_exec \
    --customise DPGAnalysis/HcalNanoAOD/customiseHcalCalib_cff.customiseHcalCalib
cmsRun cmsdriver_XXXXXX.py
