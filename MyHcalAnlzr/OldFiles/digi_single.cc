#include "TROOT.h"
#include "TFile.h"
#include "TNtuple.h"
#include "TCanvas.h"
#include "TH2.h"
#include "TF1.h"
#include "TProfile.h"
#include "TLegend.h"
#include "TGraph.h"

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <math.h>
#include <assert.h> 
#include <iomanip>

#include <stdlib.h>

using namespace std;

int main(int argc, char *argv[])
{
  if(argc!=6){
    cerr << "Invalid arguments provided, correct format is: ./main kind(Full/Ped) days lumi floatday runid\n";
    exit(0);
  }

  string kind = argv[1]; // "Full" or "Ped"
  float days = atof(argv[2]); // Integer
  float lumi = atof(argv[3]); // Float
  string floatday = argv[4]; // e.g. "05.07"
  string runid = argv[5]; // Integer


  TFile *f = new TFile(("/eos/user/n/nparmar/HCAL/MyHcalAnlzr/output_LocalRuns_"+kind+"_Run"+runid+".root").c_str(), "read");
  TNtuple* qiedigi = (TNtuple*)f->Get("MyHcalAnlzr/qiedigi");
  int ntot = qiedigi->GetEntries();
  std::cout << "Reading in input file, total " << ntot << " Entries." << std::endl;
  float RunNum, LumiNum, EvtNum, ieta, iphi, depth, sumADC, type, shunt;
  qiedigi->SetBranchAddress("RunNum", &RunNum);
  qiedigi->SetBranchAddress("LumiNum", &LumiNum);
  qiedigi->SetBranchAddress("EvtNum", &EvtNum);
  qiedigi->SetBranchAddress("ieta", &ieta);
  qiedigi->SetBranchAddress("iphi", &iphi);
  qiedigi->SetBranchAddress("depth", &depth);
  qiedigi->SetBranchAddress("sumADC", &sumADC);
  qiedigi->SetBranchAddress("type", &type);
  qiedigi->SetBranchAddress("shunt", &shunt);

  TFile *ofile = new TFile(("hist_LocalOutput_run"+runid+".root").c_str(), "recreate");

  std::cout << "Creating base histograms..." << std::endl;

  string det;
  string size;
  TH1F ***** histarray;
  histarray = new TH1F****[3];
  for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
    histarray[t] = new TH1F***[82];
    if (t==0) size = "_sipmSmall";
    else if (t==1) size = "_sipmLarge";
    else size = "";
    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
      histarray[t][i] = new TH1F**[72];
      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
        histarray[t][i][j] = new TH1F*[7];
        for(int k=0; k<7; k++){ // Number of depths 1..7
          if (t==2 && (i<13 || i>68)) det = "HF";
          else if (t==2 && (i>25 && i<56)) det = "HO";
          else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
          else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
          else det = "";
          histarray[t][i][j][k] = new TH1F(("hist_run"+runid+"_subdet"+det+size+"_ieta"+to_string(i<=41?i-41:i-40)+"_iphi"+to_string(j+1)+"_depth"+to_string(k+1)).c_str(), "Pedestal per Channel; ADC; Entries", 1600, 0, 40);
        }
      }
    }
  }

  std::cout << "Looping over input events..." << std::endl;

  for(int i=0; i<ntot; i++){
    if(i%10000000==0) std::cout << i << "-th entry." << std::endl;
    qiedigi->GetEntry(i);

    if(shunt!=-1.0 and shunt!=6.0) continue; //-1.0 for global, 6.0 for local

    int ietaidx = ieta<0?ieta+41:ieta+40;
    int iphiidx = iphi-1;
    int depthidx = depth-1;
    int sipmidx = -1;
    if(type==3||type==5) sipmidx=0; // Small SiPM
    else if(type==4||type==6) sipmidx=1; // Large SiPM
    else if(type==0||type==2) sipmidx=2; // HF/HO

    //std::cout << sipmidx << ", " << ietaidx << ", " << iphiidx << ", " << depthidx << std::endl;

    if (type==3 || type==4 || type==5 || type==6){
      histarray[sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/8.0); // Average ADC of all 8 TSs, HBHE
    }else if (!(ietaidx>=26 && ietaidx<=55)){
      histarray[sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/6.0); // Average ADC of all 6 TSs, HF
    }else{
      histarray[sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/10.0); // Average ADC of all 10 TSs, HO
    }

  }


  std::cout << "Writing table..." << std::endl;

  ofstream tablefile;
  tablefile.open("Table_Run"+runid+"_"+floatday+".2022.txt");
  tablefile << setw(8) << "SubDet" << setw(8) << "SiPM" << setw(8) << "ieta" << setw(8) << "iphi" << setw(8) << "depth" << setw(12) << "Mean" << setw(12) << "RMS" << "\n";
  for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
        for(int k=0; k<7; k++){ // Number of depths 1..7
          if (histarray[t][i][j][k]->GetEntries() > 0){
            det = "";
            if (t==2 && (i<13 || i>68)) det = "HF";
            else if (t==2 && (i>25 && i<56)) det = "HO";
            else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
            else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
            if (t==2) size = "";
            else size = t==0?"Small":"Large";
            tablefile << setw(8) << det << setw(8) << size << setw(8) << (i<41?i-41:i-40) << setw(8) << (j+1) << setw(8) << (k+1) << setw(12) << histarray[t][i][j][k]->GetMean() << setw(12) << histarray[t][i][j][k]->GetRMS() << "\n";
          }
        }
      }
    }
  }
  tablefile.close();



  std::cout << "Saving results..." << std::endl;

  ofile->cd();

  for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
        for(int k=0; k<7; k++){ // Number of depths 1..7
          if (histarray[t][i][j][k]->GetEntries() > 0){
            histarray[t][i][j][k]->Write();
          }
        }
      }
    }
  }

  std::cout << "Finished writing." << std::endl;
  ofile->Close();

  std::cout << "End Job." << std::endl;
  return 0;

}


