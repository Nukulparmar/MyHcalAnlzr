dir=$1

mkdir ${dir}
python3 Plotting.py hist_LocalOutput_hadd.root daysince
mv hist_LocalOutput_hadd_daysince ${dir}/byDay
python3 Plotting.py hist_LocalOutput_hadd.root lumi
mv hist_LocalOutput_hadd_lumi ${dir}/byLumi
mkdir ${dir}/histograms
rm ${dir}/byDay/Ped*
mv ${dir}/byLumi/Ped* ${dir}/histograms
mkdir ${dir}/extrapolations
mv ${dir}/byLumi/Ex* ${dir}/extrapolations
mkdir ${dir}/extrapolations_FC2ADC
mv ${dir}/extrapolations/*FC2ADC* ${dir}/extrapolations_FC2ADC

mv Table*txt /eos/user/n/nparmar/HCAL/MyHcalAnlzr/PED_tables/
# Ensure EOS directories exist
mkdir -p /eos/user/n/nparmar/www/PED_plots/byDay
mkdir -p /eos/user/n/nparmar/www/PED_plots/byLumi
mkdir -p /eos/user/n/nparmar/www/PED_plots/histograms
mkdir -p /eos/user/n/nparmar/www/PED_plots/extrapolations
mkdir -p /eos/user/n/nparmar/www/PED_plots/extrapolations_FC2ADC

mv ${dir}/byDay/* /eos/user/n/nparmar/www/PED_plots/byDay/
mv ${dir}/byLumi/* /eos/user/n/nparmar/www/PED_plots/byLumi/
mv ${dir}/histograms/* /eos/user/n/nparmar/www/PED_plots/histograms/
mv ${dir}/extrapolations/* /eos/user/n/nparmar/www/PED_plots/extrapolations/
mv ${dir}/extrapolations_FC2ADC/* /eos/user/n/nparmar/www/PED_plots/extrapolations_FC2ADC/
rm -r ${dir}
