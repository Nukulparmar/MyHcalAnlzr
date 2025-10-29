# MyHcalAnlzr

## Step 1

Get the data:
```
cmsRun localrun.py
```
... after editing the `localrun.py` file to include all runs you want to process. Also set the output filename.

## Step 2

Process the data to get histograms. First, compile the `digi.cc`:
```
g++ -Wall -g `root-config --glibs --cflags` digi.cc -o macro
```
... again, after hardcoding the same runs into the `digi.cc` that were processed in the first step. Also add the corresponding day (as float), number of days since the beginning of Run3, and also the recorded lumi an that day.

Then run:
```
./macro /eos/user/n/nparmar/HCAL/MyHcalAnlzr/output_LocalRuns_set1 LocalOutput_set1
```

Optional: `hadd` the output with previous outputs. Some values are stored in a separate files to make graphs from all previously processed output.

## Step 3

Make the plots:
```
python3 Plotting.py LocalOutput_set1.root
```
Optional second arguments set what is on the x-axis of the plots: Either the luminosity (`lumi`) or the date (as either float (`floatday`) or days since beginning (`daysince`)).

Optional additional arguments after that are run numbers for which to plot histograms.
