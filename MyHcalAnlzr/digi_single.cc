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
  //float days = atof(argv[2]); // Integer
  float lumi = atof(argv[3]); // Float
  string floatday = argv[4]; // e.g. "05.07"
  string runid = argv[5]; // Integer


  TFile *f = new TFile(("/eos/user/n/nparmar/HCAL/MyHcalAnlzr/output_LocalRuns_"+kind+"_Run"+runid+".root").c_str(), "read");
  TNtuple* qiedigi = (TNtuple*)f->Get("MyHcalAnlzr/qiedigi");
  int ntot = qiedigi->GetEntries();
  std::cout << "Reading in input file, total " << ntot << " Entries." << std::endl;
  float RunNum, LumiNum, EvtNum, ieta, iphi, depth, sumADC, sumFC, type, shunt;
  qiedigi->SetBranchAddress("RunNum", &RunNum);
  qiedigi->SetBranchAddress("LumiNum", &LumiNum);
  qiedigi->SetBranchAddress("EvtNum", &EvtNum);
  qiedigi->SetBranchAddress("ieta", &ieta);
  qiedigi->SetBranchAddress("iphi", &iphi);
  qiedigi->SetBranchAddress("depth", &depth);
  qiedigi->SetBranchAddress("sumADC", &sumADC);
  qiedigi->SetBranchAddress("sumFC", &sumFC);
  qiedigi->SetBranchAddress("type", &type);
  qiedigi->SetBranchAddress("shunt", &shunt);

  TFile *ofile = new TFile(("hist_LocalOutput_run"+runid+".root").c_str(), "recreate");

  std::cout << "Creating base histograms..." << std::endl;

  string det;
  string size;
  TH1F ****** histarray;
  histarray = new TH1F*****[2];
  for(int u=0; u<2; u++){ // 0=ADC, 1=FC
    histarray[u] = new TH1F****[3];
    for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
      histarray[u][t] = new TH1F***[82];
      if (t==0) size = "_sipmSmall";
      else if (t==1) size = "_sipmLarge";
      else size = "";
      for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
        histarray[u][t][i] = new TH1F**[72];
        for(int j=0; j<72; j++){ // Number of iphi bins 1..72
          histarray[u][t][i][j] = new TH1F*[7];
          for(int k=0; k<7; k++){ // Number of depths 1..7
            if (t==2 && (i<13 || i>68)) det = "HF";
            else if (t==2 && (i>25 && i<56)) det = "HO";
            else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
            else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
            else det = "";
            if (u==0){
              histarray[u][t][i][j][k] = new TH1F(("hist_run"+runid+"_subdet"+det+size+"_ieta"+to_string(i<=41?i-41:i-40)+"_iphi"+to_string(j+1)+"_depth"+to_string(k+1)+"_ADC").c_str(), "Pedestal per Channel; ADC; Entries", 960, 0, 32);
            }else{
              histarray[u][t][i][j][k] = new TH1F(("hist_run"+runid+"_subdet"+det+size+"_ieta"+to_string(i<=41?i-41:i-40)+"_iphi"+to_string(j+1)+"_depth"+to_string(k+1)+"_FC").c_str(), "Pedestal per Channel; FC; Entries", 10000, 0, 1000);
            }
          }
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
      histarray[0][sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/8.0); // Average ADC of all 8 TSs, HBHE
      histarray[1][sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumFC/8.0);
    }else if (!(ietaidx>=26 && ietaidx<=55)){
      histarray[0][sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/6.0); // Average ADC of all 6 TSs, HF
      histarray[1][sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumFC/6.0);
    }else{
      histarray[0][sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumADC/10.0); // Average ADC of all 10 TSs, HO
      histarray[1][sipmidx][ietaidx][iphiidx][depthidx]->Fill(sumFC/10.0);
    }

  }


  // std::cout << "Writing table..." << std::endl;

  // // ofstream tablefile;
  // // tablefile.open("Table_Run"+runid+"_"+floatday+".2025.txt");
  // // tablefile << setw(8) << "SubDet" << setw(8) << "SiPM" << setw(8) << "ieta" << setw(8) << "iphi" << setw(8) << "depth" << setw(12) << "ADC Mean" << setw(12) << "ADC RMS" << setw(12) << "fC Mean" << setw(12) << "fC RMS" << "\n";
  // // for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
  // //   for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
  // //     for(int j=0; j<72; j++){ // Number of iphi bins 1..72
  // //       for(int k=0; k<7; k++){ // Number of depths 1..7
  // //         if (histarray[0][t][i][j][k]->GetEntries() > 0){
  // //           det = "";
  // //           if (t==2 && (i<13 || i>68)) det = "HF";
  // //           else if (t==2 && (i>25 && i<56)) det = "HO";
  // //           else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
  // //           else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
  // //           if (t==2) size = "";
  // //           else size = t==0?"Small":"Large";
  // //           tablefile << setw(8) << det << setw(8) << size << setw(8) << (i<41?i-41:i-40) << setw(8) << (j+1) << setw(8) << (k+1) << setw(12) << histarray[0][t][i][j][k]->GetMean() << setw(12) << histarray[0][t][i][j][k]->GetRMS() << setw(12) << histarray[1][t][i][j][k]->GetMean() << setw(12) << histarray[1][t][i][j][k]->GetRMS() << "\n";
  // //         }
  // //       }
  // //     }
  // //   }
  // // }
  // // tablefile.close();
  std::cout << "Writing table..." << std::endl;

  ofstream tablefile;
  tablefile.open("Table_Run"+runid+"_"+floatday+".2025.txt");
  tablefile << setw(8) << "SubDet" << setw(8) << "SiPM" << setw(8) << "ieta" << setw(8) << "iphi" << setw(8) << "depth" << setw(12) << "Lumi" << setw(12) << "ADC Mean" << setw(12) << "ADC RMS" << setw(12) << "fC Mean" << setw(12) << "fC RMS" << "\n";
  for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
    for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
      for(int j=0; j<72; j++){ // Number of iphi bins 1..72
        for(int k=0; k<7; k++){ // Number of depths 1..7
          if (histarray[0][t][i][j][k]->GetEntries() > 0){
            det = "";
            if (t==2 && (i<13 || i>68)) det = "HF";
            else if (t==2 && (i>25 && i<56)) det = "HO";
            else if (t<2 && ((i>=26 && i<=55) || (i==25 && k<3) || (i==56 && k<3))) det = "HB";
            else if (t<2 && ((i>=12 && i<=24) || (i>=57 && i<=69) || (i==25 && k>=3) || (i==56 && k>=3))) det = "HE";
            if (t==2) size = "";
            else size = t==0?"Small":"Large";
            tablefile << setw(8) << det << setw(8) << size << setw(8) << (i<41?i-41:i-40) << setw(8) << (j+1) << setw(8) << (k+1) << setw(12) << lumi << setw(12) << histarray[0][t][i][j][k]->GetMean() << setw(12) << histarray[0][t][i][j][k]->GetRMS() << setw(12) << histarray[1][t][i][j][k]->GetMean() << setw(12) << histarray[1][t][i][j][k]->GetRMS() << "\n";
          }
        }
      }
    }
  }
  tablefile.close();

  ////
  std::cout << "Preparing matching map..." << std::endl; // Find eta/phi/depth matching to crate/slot/fiber/channel, for HBHE only (Reminder that some eta/phi/depth overlap between HBHE and HFHO)
  map<string, string> matching;
  ifstream infile("lmap_complete.txt"); 
  string line, sumone, sumtwo, strgarbage;
  int side, eta, phi, dept, crate, slot, fiber, channel, garbage;
  vector<string> ishbhe{ "HB", "HBX", "HE", "HEX" };
  while (getline(infile, line))
  {
    istringstream iss(line);
    iss >> side;
    iss >> eta;
    iss >> phi;
    iss >> garbage; // dPhi
    iss >> dept;
    iss >> garbage; // CH_TYPE
    iss >> strgarbage; // Det
    if(find(ishbhe.begin(), ishbhe.end(), strgarbage) == ishbhe.end()) continue;
    iss >> strgarbage; // RBX
    iss >> garbage; // Wedge
    iss >> garbage; // MB_NO
    iss >> garbage; // BV
    iss >> garbage; // QIE
    iss >> garbage; // QIECH
    iss >> garbage; // RM
    iss >> garbage; // RM_FI
    iss >> channel; // FI_CH
    iss >> garbage; // Trunk
    iss >> garbage; // cpCol
    iss >> garbage; // cpRow
    iss >> garbage; // cpCpl
    iss >> garbage; // cpLC
    iss >> garbage; // cpOctFib
    iss >> garbage; // ribbon
    iss >> garbage; // ppCol
    iss >> garbage; // ppRow
    iss >> strgarbage; // ppCpl
    iss >> garbage; // ppLC
    iss >> garbage; // dodec
    iss >> crate; // Crate
    iss >> slot; // uHTR
    iss >> fiber; // uHTR_FI

    eta = eta * side;
    sumone = to_string(crate)+"_"+to_string(slot)+"_"+to_string(fiber)+"_"+to_string(channel);
    sumtwo = to_string(eta)+" "+to_string(phi)+" "+to_string(dept);
    matching[sumone] = sumtwo;
  }

  std::cout << "Writing xml..." << std::endl;

  ofstream xmlfile;
  xmlfile.open("TEST.xml");

  auto MakeNewBrick = [&xmlfile](int crate, int slot, int elements){
    xmlfile << "  <CFGBrick>" << "\n";
    xmlfile << "    <Parameter name=\"INFOTYPE\" type=\"string\">ZS</Parameter>" << "\n";
    xmlfile << "    <Parameter name=\"CREATIONTAG\" type=\"string\">hb12-13_he8_hf0_ho11_v14</Parameter>" << "\n";
    xmlfile << "    <Parameter name=\"CRATE\" type=\"int\">" << dec << crate << "</Parameter>" << "\n";
    xmlfile << "    <Parameter name=\"SLOT\" type=\"int\">" << dec << slot << "</Parameter>" << "\n";
    xmlfile << "    <Parameter name=\"TOPBOTTOM\" type=\"string\">utca</Parameter>" << "\n";
    xmlfile << "    <Parameter name=\"ZS_TYPE\" type=\"string\">standard</Parameter>" << "\n";
    xmlfile << "    <Data elements=\"" << dec << elements << "\" encoding=\"hex\">";
  };
  auto EndBrick = [&xmlfile](){
    xmlfile << "</Data>" << "\n";
    xmlfile << "  </CFGBrick>" << "\n";
  };

  xmlfile << "<?xml version=\"1.0\" ?>" << "\n";
  xmlfile << "<CFGBrickSet>" << "\n";

  // HBHE
  vector<int> HBHEcrateVec{ 20, 21, 24, 25, 30, 31, 34, 35, 37 };
  vector<int> FibNotInMod2{ 0, 1, 10, 11 };
  vector<int> FibNotInMod0{ 0, 11, 12, 23 };
  for(int crate: HBHEcrateVec){
    for(int slot=1; slot<13; slot++){
      int modulo = slot%3;
      int elements, maxchannel, ZS;
      string mystring;
      int filled = 0;
      if(modulo==0){
        maxchannel = 6;
      }else{
        maxchannel = 8;
      }
      elements = 24 * maxchannel; // 192 for HB, 144 for HE
      MakeNewBrick(crate, slot, elements);
      for(int fiber=0; fiber<24; fiber++){
        bool FiberNotInUHTR = (modulo==2 and find(FibNotInMod2.begin(), FibNotInMod2.end(), fiber) != FibNotInMod2.end()) or (modulo==0 and find(FibNotInMod0.begin(), FibNotInMod0.end(), fiber) != FibNotInMod0.end());
        for(int channel=0; channel<maxchannel; channel++){
          if((modulo==2 and fiber==10 and (channel==4 || channel==5)) || (modulo==0 and fiber==11 and (channel==0 || channel==1))){ // Nonexistent HB channels (for some reason have ZS 0 instead of 255)
            ZS = 0;
          }else if(modulo==2 and ((fiber==14 and channel==4) || (fiber==15 and channel==0) || (fiber==20 and channel==4) || (fiber==21 and channel==0))){ // Masked HE channels, RM1 RMFI6 CH4, RM2 RMFI4 CH0, RM3 RMFI6 CH4, RM4 RMFI4 CH0 (Note on ranges: RM 1-4, RMFI 1-8, CH 0-5 HE, CH 0-7 HB)
            ZS = 255;
          //}else if((modulo==2 and (fiber==2 || fiber==6) and channel==2) || (modulo==1 and (fiber==21 || fiber==23) and channel==0)){ // Masked HB channels, uHTR2 RM1 RMFI2 CH2, uHTR1 RM2 RMFI8 CH0, uHTR2 RM3 RMFI2 CH2, uHTR1 RM4 RMFI8 CH0
          //  ZS = 255;
          }else if(FiberNotInUHTR){ // Nonexistent channels
            ZS = 255;
          }else if(modulo==2 and (fiber==12 || fiber==13 || fiber==22 || fiber==23) and (channel==6 || channel==7)){ // Placeholders for HE fibers, should be 255, but were regular HE ZS 8 for some reason (keep like this for now, to test consistency)
            ZS = 8;
          }else{
            mystring = matching[to_string(crate)+"_"+to_string(slot)+"_"+to_string(fiber)+"_"+to_string(channel)];
            //if(crate==20 && slot==2) cout << to_string(crate)+"_"+to_string(slot)+"_"+to_string(fiber)+"_"+to_string(channel) << " -> " << mystring << endl;
            istringstream iss(mystring);
            int ietaidx, iphiidx, depthidx=-1000;
            while( iss >> eta >> phi >> dept ){
              ietaidx = eta<0?eta+41:eta+40;
              iphiidx = phi-1;
              depthidx = dept-1;
            }
            if(depthidx==-1000){ // No valid depth: Also Masked? HE: RM2 RMFI5 CH5, RM2 RMFI7 CH1, RM3 RMFI2 CH1, RM3 RMFI4 CH0
              ZS = 255;
            }else{
              // Example configuration: HE 8, HB small 9, HB large 10
              if (((ietaidx>=26 && ietaidx<=55) || (ietaidx==25 && depthidx<3) || (ietaidx==56 && depthidx<3)) && (depthidx>1 && depthidx<4)) ZS = 13;
              else if (((ietaidx>=26 && ietaidx<=55) || (ietaidx==25 && depthidx<3) || (ietaidx==56 && depthidx<3)) && (depthidx>-1 && depthidx<2)) ZS = 12;
              else if (((ietaidx>=12 && ietaidx<=24) || (ietaidx>=57 && ietaidx<=69) || (ietaidx==25 && depthidx>=3) || (ietaidx==56 && depthidx>=3))) ZS = 8;
              // Horizontal HB:
              if ((((crate==30) and (slot==4 || slot==5 || slot==10 || slot==11)) || ((crate==31) and (slot==1 || slot==2 || slot==7 || slot==8))) and ZS>8) ZS++;
              // ZS is Mean+RMS of each channel, rounded up
              // SiPM: Large or Small? Check both
              /*
              if ((histarray[0][ietaidx][iphiidx][depthidx]->GetEntries() > 0) and (histarray[1][ietaidx][iphiidx][depthidx]->GetEntries() == 0)){
                ZS = ceil(histarray[0][ietaidx][iphiidx][depthidx]->GetMean() + histarray[0][ietaidx][iphiidx][depthidx]->GetRMS());
              }else if ((histarray[0][ietaidx][iphiidx][depthidx]->GetEntries() == 0) and (histarray[1][ietaidx][iphiidx][depthidx]->GetEntries() > 0)){
                ZS = ceil(histarray[1][ietaidx][iphiidx][depthidx]->GetMean() + histarray[1][ietaidx][iphiidx][depthidx]->GetRMS());
              }else if ((histarray[0][ietaidx][iphiidx][depthidx]->GetEntries() == 0) and (histarray[1][ietaidx][iphiidx][depthidx]->GetEntries() == 0)){
                cout << "WARNING! NONE! " << ietaidx << " " << iphiidx << " " << depthidx << endl;
              }else if ((histarray[0][ietaidx][iphiidx][depthidx]->GetEntries() > 0) and (histarray[1][ietaidx][iphiidx][depthidx]->GetEntries() > 0)){
                cout << "WARNING! BOTH! " << ietaidx << " " << iphiidx << " " << depthidx << endl;
              }
              */
            }
          }
          xmlfile << hex << ZS;
          filled++;
          if(elements != filled) xmlfile << " ";
        }
      }
      EndBrick();
    }
  }

  // HF
  vector<int> HFcrateVec{ 22, 29, 32 };
  for(int crate: HFcrateVec){
    for(int slot=1; slot<13; slot++){
      MakeNewBrick(crate, slot, 96);
      xmlfile << "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0";
      EndBrick();
    }
  }
  MakeNewBrick(38, 9, 96);
  xmlfile << "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff";
  EndBrick();

  // HO
  vector<int> HOcrateVec{ 23, 26, 27, 38 };
  for(int crate: HOcrateVec){
    for(int slot=1; slot<10; slot++){
      if(crate!=26 and slot==9) continue;
      MakeNewBrick(crate, slot, 72);
      xmlfile << "b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b b";
      EndBrick();
    }
  }

  xmlfile << "</CFGBrickSet>" << "\n";
  xmlfile.close();
  ////



  std::cout << "Saving results..." << std::endl;

  ofile->cd();

  for(int u=0; u<2; u++){ // 0=ADC, 1=FC
    for(int t=0; t<3; t++){ // 0=Small SiPM, 1=Large SiPM, 2=HF&HO
      for(int i=0; i<82; i++){ // Number of ieta bins -41..41, excluding 0
        for(int j=0; j<72; j++){ // Number of iphi bins 1..72
          for(int k=0; k<7; k++){ // Number of depths 1..7
            if (histarray[u][t][i][j][k]->GetEntries() > 0){
              histarray[u][t][i][j][k]->Write();
            }
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


