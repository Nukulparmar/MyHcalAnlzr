# MyHcalAnlzr

This is the setup for LOCAL pedestal studies! For the GLOBAL setup, check out the "hcalNano" branch! For the WholeRun / WholeFill setup, check out the "hcalNano_WholeFill" setup. 


## General info

The setup was changed to make everything more automated. When running by yourself, just make sure that outputs are being written/read in accessible places! (I.e., not on my personal EOS space. Just `grep` for `dmroy`.)

In the file `doAbsolutelyEverything.sh` one should document the days at which local runs were taken, and what the local runs are and the integrated luminosity at the time. Comment out already processed lines and run the script to process new files

In case some steps need to be redone, uncomment everything in `doAbsolutelyEverything.sh`, and comment intermediate steps not required to be redone (such as running `cmsRun`) in the script `doEverything.sh`

Before running it the first time, remember to compile first!


## How to get new data

Reminder that this specific setup is for local runs! Local runs are usually posted in elogs by the HCAL DOC who took the runs (link [here](https://cmsonline.cern.ch/webcenter/portal/cmsonline/Common/Elog?__adfpwp_action_portlet=683379043&__adfpwp_backurl=https%3A%2F%2Fcmsonline.cern.ch%3A443%2Fwebcenter%2Fportal%2Fcmsonline%2FCommon%2FElog%3F__adfpwp_mode.683379043%3D1&_piref683379043.strutsAction=%2F%2FviewSubcatMessages.do%3FcatId%3D594&fetch=1&mode=expanded&page=1&subId=9)). You need the `led-ped-Gsel-sequence` and the `Pedestal` runs. The corresponding (recorded) luminosity can be obtained from OMS (link [here](https://cmsoms.cern.ch/cms/run_3/index)).
