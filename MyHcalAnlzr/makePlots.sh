run=$1
dir="PED_plots_whole_run_${run}" # $1

# mkdir -p ${dir}
# python3 Plotting.py hist_CalibOutput_hadd.root daysince
# mv hist_CalibOutput_hadd_daysince ${dir}/byDay
# python3 Plotting.py hist_CalibOutput_hadd.root lumi
# python3 Plotting.py hist_CalibOutput_hadd_lumi.root wholerun
# # python3 Plotting.py hist_CalibOutput_hadd_${run}.root wholerun
# mv hist_CalibOutput_hadd_lumi ${dir}/byLumi
# mkdir ${dir}/histograms
# # rm ${dir}/byDay/Ped*
# mv ${dir}/byLumi/Ped* ${dir}/histograms
#mkdir ${dir}/extrapolations
##rm ${dir}/byDay/Ex*
#mv ${dir}/byLumi/Ex* ${dir}/extrapolations

python3 Plotting.py ${run} wholerun

# mv ${dir}/byDay/* /eos/user/n/nparmar/www/plots_archive/PED_plots_2023/byDay/
mkdir -p /eos/user/n/nparmar/www/${dir}
mkdir -p /eos/user/n/nparmar/www/${dir}/byLumi/

mv WholeRunOutput_${run}/Table*txt  /eos/user/n/nparmar/www/${dir}/  
mv WholeRunOutput_${run}/PedestalTable*txt /eos/user/n/nparmar/www/${dir}
mv WholeRunOutput_${run}/*.pdf /eos/user/n/nparmar/www/${dir}/byLumi/
mv WholeRunOutput_${run}/*.png /eos/user/n/nparmar/www/${dir}/byLumi/
mkdir -p /eos/user/n/nparmar/www/${dir}/histograms/
mv WholeRunOutput_${run}/*.root /eos/user/n/nparmar/www/${dir}/histograms/
#mv ${dir}/extrapolations/* /eos/user/n/nparmar/www/plots_archive/PED_plots_2023/extrapolations/
