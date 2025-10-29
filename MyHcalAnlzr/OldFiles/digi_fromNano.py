import ROOT
import os, sys
from array import array

#string kind = argv[1]; // "Full" or "Ped"
#float days = atof(argv[2]); // Integer
#float lumi = atof(argv[3]); // Float
floatday = "22.02"; #argv[4]; // e.g. "05.07"
runid = "363781" #argv[5]; // Integer

f = ROOT.TFile.Open("/eos/user/n/nparmar/HCAL/MyHcalAnlzr_Nano/output_CalibRuns_Nano_Run"+runid+".root", "read")
qiedigi = f.Get("Events")
ntot = qiedigi.GetEntries()
print("Reading in input file, total "+str(ntot)+" Events." )
subdets = {"HB": 8, "HE": 8, "HF": 3, "HO": 10} # Subdet and corresponding number of TS
ofile = ROOT.TFile.Open("hist_CalibOutput_run"+runid+".root", "recreate")

print("Creating base histograms, and looping over input events...")
histarrayFC = {}
histarrayADC = {}
#for t in range(3): # 0=Small SiPM, 1=Large SiPM, 2=HF&HO
#    histarray[t] = new TH1F***[82];
#    if (t==0) size = "_sipmSmall";
#    else if (t==1) size = "_sipmLarge";
#    else size = "";
#    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
#      histarray[t][i] = new TH1F**[72];
#      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
#        histarray[t][i][j] = new TH1F*[7];
#        for(int k=0; k<7; k++){ // Number of depths 1..7
#          if (t==2 && (i<13 || i>68)) det = "HF";
#          else if (t==2 && (i>25 && i<56)) det = "HO";
#          else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
#          else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
#          else det = "";
#          histarray[t][i][j][k] = new TH1F(("hist_run"+runid+"_subdet"+det+size+"_ieta"+to_string(i<=41?i-41:i-40)+"_iphi"+to_string(j+1)+"_depth"+to_string(k+1)).c_str(), "Pedestal per Channel; ADC; Entries", 1600, 0, 40);
#        }
#      }
#    }
#  }*/

for i in range(ntot):
  if i%100==0: print(str(i)+"-th event.")
  qiedigi.GetEntry(i)

  # Subdet, SiPM size, ieta, iphi, depth
  for subdet in subdets:
    nchannel = int(qiedigi.GetLeaf("nDigi"+subdet).GetValue())
    if subdet not in histarrayFC:
      histarrayFC[subdet] = {}
      histarrayADC[subdet] = {}
    for j in range(nchannel):
      size = "" # TODO
      ieta = int(qiedigi.GetLeaf("Digi"+subdet+"_ieta").GetValue(j))
      iphi = int(qiedigi.GetLeaf("Digi"+subdet+"_iphi").GetValue(j))
      depth = int(qiedigi.GetLeaf("Digi"+subdet+"_depth").GetValue(j))
      if size not in histarrayFC[subdet]:
        histarrayFC[subdet][size] = {}
        histarrayADC[subdet][size] = {}
      if ieta not in histarrayFC[subdet][size]:
        histarrayFC[subdet][size][ieta] = {}
        histarrayADC[subdet][size][ieta] = {}
      if iphi not in histarrayFC[subdet][size][ieta]:
        histarrayFC[subdet][size][ieta][iphi] = {}
        histarrayADC[subdet][size][ieta][iphi] = {}
      if depth not in histarrayFC[subdet][size][ieta][iphi]:
        histarrayFC[subdet][size][ieta][iphi][depth] = ROOT.TH1F("hist_run"+runid+"_subdet"+subdet+size+"_ieta"+str(ieta)+"_iphi"+str(iphi)+"_depth"+str(depth)+"_FC", "Pedestal per Channel; fC; Entries", 1600, 0, 40) # TODO: Adjust range
        histarrayADC[subdet][size][ieta][iphi][depth] = ROOT.TH1F("hist_run"+runid+"_subdet"+subdet+size+"_ieta"+str(ieta)+"_iphi"+str(iphi)+"_depth"+str(depth)+"_ADC", "Pedestal per Channel; ADC; Entries", 1600, 0, 40) # TODO: Adjust range
      for TS in range(subdets[subdet]):
        histarrayFC[subdet][size][ieta][iphi][depth].Fill(qiedigi.GetLeaf("Digi"+subdet+"_fc"+str(TS)).GetValue(j))
        histarrayADC[subdet][size][ieta][iphi][depth].Fill(qiedigi.GetLeaf("Digi"+subdet+"_adc"+str(TS)).GetValue(j))

#    //if(shunt!=-1.0 and shunt!=6.0) continue; //-1.0 for global, 6.0 for local
#
#    //int ietaidx = ieta<0?ieta+41:ieta+40;
#    //int iphiidx = iphi-1;
#    //int depthidx = depth-1;
#    //int sipmidx = -1;
#    //if(type==3||type==5) sipmidx=0; // Small SiPM
#    //else if(type==4||type==6) sipmidx=1; // Large SiPM
#    //else if(type==0||type==2) sipmidx=2; // HF/HO
#
#    //std::cout << sipmidx << ", " << ietaidx << ", " << iphiidx << ", " << depthidx << std::endl;
#
#    /*if (type==3 || type==4 || type==5 || type==6){
#      histarray[sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/8.0); // Average ADC of all 8 TSs, HBHE
#    }else if (!(ietaidx>=26 && ietaidx<=55)){
#      histarray[sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/6.0); // Average ADC of all 6 TSs, HF
#    }else{
#      histarray[sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/10.0); // Average ADC of all 10 TSs, HO
#    }*/
#  }

#  /*std::cout << "Writing table..." << std::endl;
#
#  ofstream tablefile;
#  tablefile.open("Table_Run"+runid+"_"+floatday+".2022.txt");
#  tablefile << setw(8) << "SubDet" << setw(8) << "SiPM" << setw(8) << "ieta" << setw(8) << "iphi" << setw(8) << "depth" << setw(12) << "Mean" << setw(12) << "RMS" << "\n";
#  for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
#    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
#      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
#        for(int k=0; k<7; k++){ // Number of depths 1..7
#          if (histarray[t][i][j][k]->GetEntries() > 0){
#            det = "";
#            if (t==2 && (i<13 || i>68)) det = "HF";
#            else if (t==2 && (i>25 && i<56)) det = "HO";
#            else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
#            else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
#            if (t==2) size = "";
#            else size = t==0?"Small":"Large";
#            tablefile << setw(8) << det << setw(8) << size << setw(8) << (i<41?i-41:i-40) << setw(8) << (j+1) << setw(8) << (k+1) << setw(12) << histarray[t][i][j][k]->GetMean() << setw(12) << histarray[t][i][j][k]->GetRMS() << "\n";
#          }
#        }
#      }
#    }
#  }
#  tablefile.close();*/



print("Saving results...")

ofile.cd()
for subdet in histarrayFC:
  for size in histarrayFC[subdet]:
    for eta in histarrayFC[subdet][size]:
      for phi in histarrayFC[subdet][size][eta]:
        for depth in histarrayFC[subdet][size][eta][phi]:
          histarrayFC[subdet][size][eta][phi][depth].Write()
          histarrayADC[subdet][size][eta][phi][depth].Write()

#  /*for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
#    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
#      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
#        for(int k=0; k<7; k++){ // Number of depths 1..7
#          if (histarray[t][i][j][k]->GetEntries() > 0){
#            histarray[t][i][j][k]->Write();
#          }
#        }
#      }
#    }
#  }*/

print("Finished writing.")
ofile.Close()
print("End Job.")
exit(0)


