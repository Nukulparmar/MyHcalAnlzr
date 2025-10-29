#!/usr/bin/env python
# coding: utf-8

# In[1]:


import ROOT
import os, sys
from array import array


def ReadSaveFile(savefilename):
  with open(savefilename) as savefile:
    lines = [line.rstrip() for line in savefile]
  if lines != sorted(lines): # Sort file
    print("Going to sort")
    os.system('mv '+savefilename+' '+savefilename+'_old')
    # First remove duplicate entries with different result: Save newer one
    lines2 = []
    contains = []
    for l in lines:
      category = l.split()[:-1]
      if category not in contains:
        contains.append(category)
      else:
        delme=""
        for k in lines2:
          if k.split()[:-1]==category and k!=l:
            delme=k
            break
        if delme!="":
          lines2.remove(delme)
          #print('Going to replace "',delme,'" with "',l,'"')
      lines2.append(l)
    lastline = ""
    with open(savefilename, 'w') as savefile:
      for l in sorted(lines2):
        if l==lastline: continue # Remove exact duplicates
        if l.split()[-1] == "0": continue # Ignore empty entries
        savefile.write(l+"\n")
        lastline = l

  values = {}
  for l in lines:
    stuff = l.split(" ")
    runnr = stuff[0]
    #lumi = stuff[1]
    #daysince = stuff[2]
    #date = stuff[3]
    ID = stuff[1]+"_"+stuff[2]+"_"+stuff[3]
    trendtype = stuff[4]
    meanrms = stuff[5]
    if trendtype not in values: values[trendtype] = {}
    if ID not in values[trendtype]:
      #if len(values[trendtype])>0: # Wanted to check if either lumi, date, daysince are inconsistent for a single day. (But two runs may exist for one day: Full and Ped run)
      #  print("Something is weird!")
      #  print(ID)
      #  print(values[trendtype])
      values[trendtype][ID] = {}
    if meanrms not in values[trendtype][ID]: values[trendtype][ID][meanrms] = {}
    values[trendtype][ID][meanrms][runnr] = float(stuff[6])

  return values

def MakeGraph(values, trendtype, meanrms, what): # what in ["daysince", "lumi", "wholerun"]
  allvals = {}
  for ID in values[trendtype]:
    yval = 0.0
    for runnr in values[trendtype][ID][meanrms]:
      yval += values[trendtype][ID][meanrms][runnr]
    yval = yval / len(values[trendtype][ID][meanrms])
    if what=="daysince":
      xval = int(ID.split("_")[1])
    elif what=="lumi":
      xval = float(ID.split("_")[0])
    elif what=="wholerun":
      xval = int(ID.split("_")[0])
    allvals[xval] = yval

  x = []
  y = []
  for key, value in sorted(allvals.items()):
    x.append(key)
    y.append(value)
  if len(x)==0: return None
  gr = ROOT.TGraph(len(x), array('d', x), array('d', y))
  return gr

def GetDay(run):
  with open('SaveFile.txt') as savefile:
    lines = [line.rstrip() for line in savefile]
  for l in lines:
    if l.startswith(run):
      return l.split()[3]

def MinMaxAxis(minv, maxv, mindist):
  thismin = min(minv)
  thismax = max(maxv)
  if thismax-thismin < mindist:
    diff = mindist - (thismax-thismin)
    thismax += diff/2
    thismin -= diff/2
  if thismin - (thismax-thismin)*0.2 < 0:
    thismin = thismax*0.2/1.2
  return thismin, thismax

#adc2fC = [ # https://github.com/cms-sw/cmssw/blob/f5b4310413558919869e0dfa7c9c231e4b2b03fc/DQM/HcalCommon/interface/Constants.h#L253
#        1.58,   4.73,   7.88,   11.0,   14.2,   17.3,   20.5,   23.6,   26.8,   29.9,   33.1,   36.2,   39.4,
#        42.5,   45.7,   48.8,   53.6,   60.1,   66.6,   73.0,   79.5,   86.0,   92.5,   98.9,   105,    112,
#        118,    125,    131,    138,    144,    151,    157,    164,    170,    177]
#adc2fc_graph = ROOT.TGraph(len(adc2fC), array('d', range(len(adc2fC))), array('d', adc2fC))
#fc2adc_graph = ROOT.TGraph(len(adc2fC), array('d', adc2fC), array('d', range(len(adc2fC))))

#fc2adc_fit = ROOT.TF1( 'fc2adc_fit', "([2]+[3]*x)*(x<45.7) + ([4]+[5]*x)*(x>53.6) + (([2]+[3]*x)*(53.6-x)/(53.6-45.7)+([4]+[5]*x)*(x-45.7)/(53.6-45.7))*(x>=45.7)*(x<=53.6)", 0, 180)
#fc2adc_fit.SetParameter(2,1.58)
#fc2adc_fit.SetParameter(3,3.15)
#fc2adc_fit.SetParameter(4,-50)
#fc2adc_fit.SetParameter(5,6.3)
#fc2adc_graph.Fit("fc2adc_fit", "F")

#def ADCtoFC(adc):
#  return adc2fc_graph.Eval(adc)

#def FCtoADC(fc):
#  return fc2adc_graph.Eval(fc)

def MakeExtrapolation(gr, trend):
  N = gr[trend]["MeanMean"].GetN()
  x = []
  y = []
  e = []
  for i in range(N):
    x.append(gr[trend]["MeanMean"].GetPointX(i))
    y.append(gr[trend]["MeanMean"].GetPointY(i))
    y[-1] += 2*gr[trend]["MeanRMS"].GetPointY(i)
    y[-1] += 2*gr[trend]["RMSMean"].GetPointY(i)
    y[-1] += 2*gr[trend]["RMSRMS"].GetPointY(i)
    e.append(N-i)
  gr = ROOT.TGraph(len(x), array('d', x), array('d', y))
  grerr = ROOT.TGraphErrors(len(x), array('d', x), array('d', y), array('d', e), array('d', e))
  return gr, grerr

def MakeChargeExtrapolation(gr, trend):
  N = gr[trend]["MeanMean"].GetN()
  x = []
  y = []
  e = []
  for i in range(N):
    x.append(gr[trend]["MeanMean"].GetPointX(i))
    #fc = ADCtoFC(gr[trend]["MeanMean"].GetPointY(i))
    #fc += 2*ADCtoFC(gr[trend]["MeanRMS"].GetPointY(i))
    #fc += 2*ADCtoFC(gr[trend]["RMSMean"].GetPointY(i))
    #fc += 2*ADCtoFC(gr[trend]["RMSRMS"].GetPointY(i))
    fc = gr[trend]["MeanMean"].GetPointY(i)
    fc += 2*gr[trend]["MeanRMS"].GetPointY(i)
    fc += 2*gr[trend]["RMSMean"].GetPointY(i)
    fc += 2*gr[trend]["RMSRMS"].GetPointY(i)
    fc = ADCtoFC(fc)
    y.append(fc)
    e.append(N-i)
  gr = ROOT.TGraph(len(x), array('d', x), array('d', y))
  grerr = ROOT.TGraphErrors(len(x), array('d', x), array('d', y), array('d', e), array('d', e))
  return gr, grerr


##### Start
ROOT.gStyle.SetOptFit(1)
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)
if len(sys.argv)>1:
  inputfile = sys.argv[1]
else:
  inputfile = "hist_CalibOutput_hadd.root"
#fin.ls()

if len(sys.argv)>2 and sys.argv[2] in ["daysince", "lumi", "wholerun"]:
  dowhat = sys.argv[2]
else:
  dowhat = "daysince"

if dowhat!="wholerun":
  output = inputfile.split(".")[0]+"_"+dowhat+"/"
  if not os.path.isdir(output): os.mkdir(output)
  fin=ROOT.TFile.Open(inputfile, "READ")
else:
  output = "WholeRunOutput_"+inputfile+"/"

savefilename = 'SaveFile.txt'
if dowhat == "daysince":
  xtitle = "Days since 6th April 2025" #"Days since 5th July"
elif dowhat == "lumi":
  xtitle = "Luminosity [fb^{-1}]"
elif dowhat == "wholerun":
  # fall back to the first argument if that's how you invoked the script.
  run_for_title = sys.argv[3] if len(sys.argv) > 3 else (sys.argv[1] if len(sys.argv) > 1 else "UNKNOWN")
  xtitle = f"Luminosity section [Run - {run_for_title}]"
  savefilename = 'SaveFile_'+inputfile+'.txt'

runstoplot = []
if len(sys.argv)>3:
  runstoplot = sys.argv[3:]


##### Prepare trend plots
values = ReadSaveFile(savefilename)
trends = []
for trend in values:
  if trend not in trends: trends.append(trend)
trends = sorted(trends)

gr = {}
limits = {}
allmeanrms = ["MeanMean", "MeanRMS", "RMSMean", "RMSRMS"]
for trend in trends:
  gr[trend] = {}
  for meanrms in allmeanrms:
    limits[trend+meanrms] = [999, 0]
    gr[trend][meanrms] = MakeGraph(values, trend, meanrms, dowhat)
    if gr[trend][meanrms] is None: continue
    thismin = ROOT.TMath.MinElement(gr[trend][meanrms].GetN(), gr[trend][meanrms].GetY())
    thismax = ROOT.TMath.MaxElement(gr[trend][meanrms].GetN(), gr[trend][meanrms].GetY())
    if limits[trend+meanrms][0] > thismin: limits[trend+meanrms][0] = thismin
    if limits[trend+meanrms][1] < thismax: limits[trend+meanrms][1] = thismax


grdict = {}
for subdet in ["HB", "HE", "HF", "HO"]:
  grdict["Mean of per-channel pedestal Mean in "+subdet] = ["MeanMean", subdet]
  grdict["Mean of per-channel pedestal RMS in "+subdet] = ["MeanRMS", subdet]
  grdict["RMS of per-channel pedestal Mean in "+subdet] = ["RMSMean", subdet]
  grdict["RMS of per-channel pedestal RMS in "+subdet] = ["RMSRMS", subdet]
c = []
legend = []

##### Draw PED trends
for title in grdict:
  for unit in ["ADC", "FC"]:
    c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 800, 800 ))
    c[-1].SetLeftMargin(0.12)
    c[-1].cd()
    legend.append(ROOT.TLegend(0.12,0.8,0.9,0.9))
    legend[-1].SetNColumns(2)
    meanrms = grdict[title][0]
    subdet = grdict[title][1]
    parts = [trend for trend in trends if trend.startswith(subdet) and trend.endswith(unit) and "depth" not in trend]
    # Manually sort:
    # if parts == ['HB_sipmLarge_'+unit, 'HB_sipmLarge_HBM09RM3_'+unit, 'HB_sipmLarge_HBP14RM1_'+unit, 'HB_sipmLarge_phi,1,72_'+unit, 'HB_sipmLarge_phi,18,19_'+unit, 'HB_sipmLarge_phi,36,37_'+unit, 'HB_sipmSmall_'+unit, 'HB_sipmSmall_HBM09RM3_'+unit, 'HB_sipmSmall_HBP14RM1_'+unit, 'HB_sipmSmall_phi,1,72_'+unit, 'HB_sipmSmall_phi,18,19_'+unit, 'HB_sipmSmall_phi,36,37_'+unit]:
    #   parts = ['HB_sipmLarge_'+unit, 'HB_sipmSmall_'+unit, 'HB_sipmLarge_phi,1,72_'+unit, 'HB_sipmSmall_phi,1,72_'+unit, 'HB_sipmLarge_phi,36,37_'+unit, 'HB_sipmSmall_phi,36,37_'+unit, 'HB_sipmLarge_HBP14RM1_'+unit, 'HB_sipmSmall_HBP14RM1_'+unit, 'HB_sipmLarge_HBM09RM3_'+unit, 'HB_sipmSmall_HBM09RM3_'+unit] # , 'HB_sipmLarge_phi,18,19_'+unit, 'HB_sipmSmall_phi,18,19_'+unit
    # if parts == ['HE_sipmLarge_'+unit, 'HE_sipmLarge_phi,1,72_'+unit, 'HE_sipmLarge_phi,18,19_'+unit, 'HE_sipmLarge_phi,36,37_'+unit, 'HE_sipmSmall_'+unit, 'HE_sipmSmall_phi,1,72_'+unit, 'HE_sipmSmall_phi,18,19_'+unit, 'HE_sipmSmall_phi,36,37_'+unit]:
    #   parts = ['HE_sipmLarge_'+unit, 'HE_sipmSmall_'+unit, 'HE_sipmLarge_phi,1,72_'+unit, 'HE_sipmSmall_phi,1,72_'+unit, 'HE_sipmLarge_phi,36,37_'+unit, 'HE_sipmSmall_phi,36,37_'+unit] # , 'HE_sipmLarge_phi,18,19_'+unit, 'HE_sipmSmall_phi,18,19_'+unit
    
    thismin, thismax = MinMaxAxis((limits[trend+meanrms][0] for trend in parts), (limits[trend+meanrms][1] for trend in parts), 0.5)
    # if subdet=="HB": color = ROOT.kBlue
    # elif subdet=="HE": color = ROOT.kGreen
    # elif subdet=="HF": color = ROOT.kRed
    # elif subdet=="HO": color = ROOT.kBlack
    if subdet=="HB":
        parts = ['HB_sipmLarge_'+unit, 'HB_sipmSmall_'+unit,  'HB_sipmLarge_HBP14RM1_'+unit,'HB_sipmSmall_HBP14RM1_'+unit, 'HB_sipmLarge_HBM09RM3_'+unit, 'HB_sipmSmall_HBM09RM3_'+unit, 'HB_sipmLarge_HBM04RM3_'+unit, 'HB_sipmSmall_HBM04RM3_'+unit, 'HB_sipmLarge_HBM12RM3_'+unit, 'HB_sipmSmall_HBM12RM3_'+unit]
        color = ROOT.kBlue
    elif subdet=="HE":
        parts = ['HE_sipmLarge_'+unit, 'HE_sipmSmall_'+unit]
        color = ROOT.kGreen
    elif subdet=="HF": color = ROOT.kRed
    elif subdet=="HO":
        parts = ['HO_'+unit, 'HO_HO0_'+unit, 'HO_HO1_'+unit, 'HO_HO2_'+unit]
        color = ROOT.kBlack

    lowedge = 999
    upedge = 0

    # First, save individual parts as separate PDF files
    for j,part in enumerate(parts):
      if gr[part][meanrms] is None: continue
      
      # Create individual canvas for this part
      c_individual = ROOT.TCanvas( 'c_ind_'+part, 'c_ind_'+part, 800, 800 )
      c_individual.SetLeftMargin(0.12)
      c_individual.cd()
      
      # Set styling for individual plot
      if "HB" in part or "HE" in part:
        if "Large" in part: tcolor = ROOT.kBlue
        if "Small" in part: tcolor = ROOT.kGreen
      else:
        tcolor = color
        
      if "phi,1," in part:
        tcolor = tcolor+3
        marker = 22
        line = 4
      elif "phi,36," in part:
        tcolor = tcolor-5
        marker = 23
        line = 5
      elif "phi,12," in part:
        tcolor = tcolor-7
        marker = 20
        line = 6
      elif "HBP14RM1" in part:
        tcolor = tcolor+4
        marker = 33
        line = 7
      elif "HBM09RM3" in part:
        tcolor = tcolor+4
        marker = 34
        line = 8
      elif "HBM04RM3" in part:
        tcolor = tcolor+4
        marker = 35
        line = 9
      elif "HBM12RM3" in part:
        tcolor = tcolor+4
        marker = 36
        line = 10
      elif "HO0" in part:
        tcolor = tcolor+6
        marker = 22
        line = 4
      elif "HO1" in part:
        tcolor = tcolor+2
        marker = 23
        line = 5
      elif "HO2" in part:
        tcolor = tcolor+8
        marker = 24
        line = 6
      else:
        tcolor = tcolor
        marker = 21
        line = 1

      gr[part][meanrms].SetLineColor(tcolor)
      gr[part][meanrms].SetLineStyle(line)
      gr[part][meanrms].SetMarkerStyle(marker)
      gr[part][meanrms].SetMarkerColor(tcolor)
      
      gr[part][meanrms].SetTitle(title + " - " + part)
      gr[part][meanrms].GetXaxis().SetTitle(xtitle)
      gr[part][meanrms].GetXaxis().SetDecimals()
      if unit=="ADC":
        if subdet=="HF": ytitle = "ADC (QIE10)"
        elif subdet=="HO": ytitle = "ADC (QIE8)"
        else: ytitle = "ADC (QIE11)"
      else:
        ytitle = "Q [fC]"
      gr[part][meanrms].GetYaxis().SetTitle(ytitle)
      part_min = ROOT.TMath.MinElement(gr[part][meanrms].GetN(), gr[part][meanrms].GetY())
      part_max = ROOT.TMath.MaxElement(gr[part][meanrms].GetN(), gr[part][meanrms].GetY())
      gr[part][meanrms].SetMinimum(part_min - (part_max-part_min)*0.2)
      gr[part][meanrms].SetMaximum(part_max + (part_max-part_min)*0.3)
      gr[part][meanrms].Draw("APL")
      
      # Save individual plot
      c_individual.SaveAs(output+title.replace(" ", "_")+"_"+unit+"_"+part.replace(",", "_").replace("/", "_")+".pdf")
      c_individual.SaveAs(output+title.replace(" ", "_")+"_"+unit+"_"+part.replace(",", "_").replace("/", "_")+".png")
      del c_individual

    # Now continue with combined plot as before
    for j,part in enumerate(parts):
      if gr[part][meanrms] is None: continue
      if "HB" in part or "HE" in part:
        if "Large" in part: color = ROOT.kBlue
        if "Small" in part: color = ROOT.kGreen
      if "phi,1," in part:
        tcolor = color+3
        marker = 22
        line = 4
      elif "phi,36," in part:
        tcolor = color-5
        marker = 23
        line = 5
      elif "phi,12," in part:
        tcolor = color-7
        marker = 20
        line = 6
      elif "HBP14RM1" in part:
        tcolor = color+4
        marker = 33
        line = 7
      elif "HBM09RM3" in part:
        tcolor = color+4
        marker = 34
        line = 8
      elif "HBM04RM3" in part:
        tcolor = color+4
        marker = 35
        line = 9
      elif "HBM12RM3" in part:
        tcolor = color+4
        marker = 36
        line = 10
      elif "HO0" in part:
        tcolor = color+6
        marker = 22
        line = 4
      elif "HO1" in part:
        tcolor = color+2
        marker = 23
        line = 5
      elif "HO2" in part:
        tcolor = color+8
        marker = 24
        line = 6
      else:
        tcolor = color
        marker = 21
        line = 1

      gr[part][meanrms].SetLineColor(tcolor)
      gr[part][meanrms].SetLineStyle(line)
      gr[part][meanrms].SetMarkerStyle(marker)
      gr[part][meanrms].SetMarkerColor(tcolor)
      if j==0:
        gr[part][meanrms].SetTitle(title)
        gr[part][meanrms].GetXaxis().SetTitle(xtitle)
        gr[part][meanrms].GetXaxis().SetDecimals()
        #gr[part][meanrms].GetXaxis().SetMaxDigits(3)
        if unit=="ADC":
          if subdet=="HF": ytitle = "ADC (QIE10)"
          elif subdet=="HO": ytitle = "ADC (QIE8)"
          else: ytitle = "ADC (QIE11)"
        else:
          ytitle = "Q [fC]"
        gr[part][meanrms].GetYaxis().SetTitle(ytitle)
        gr[part][meanrms].SetMinimum(thismin - (thismax-thismin)*0.2)
        gr[part][meanrms].SetMaximum(thismax + (thismax-thismin)*0.3)
        gr[part][meanrms].Draw()
      else:
        gr[part][meanrms].Draw("PL same")
      lowedge = min(lowedge, gr[part][meanrms].GetXaxis().GetBinLowEdge(gr[part][meanrms].GetXaxis().GetFirst()))
      upedge = max(upedge, gr[part][meanrms].GetXaxis().GetBinUpEdge(gr[part][meanrms].GetXaxis().GetLast()))
      # Legend
      sizename = "PMT" if subdet=="HF" else "SiPM"
      # if subdet in ["HB", "HE"]:
      #   if "Small" in part: sizename = "Small SiPM"
      #   elif "Large" in part: sizename = "Large SiPM"
      #   if "phi,36," in part: sizename += ", iphi in [36,37]"
      #   elif "phi,18," in part: sizename += ", iphi in [18,19]"
      #   elif "phi,1," in part: sizename += ", iphi in [72,1]"
      #   elif "HBP14RM1" in part: sizename += ", HBP14 RM1"
      #   elif "HBM09RM3" in part: sizename += ", HBM09 RM3"
      if subdet in ["HB", "HE"]:
        if "Small" in part: sizename = "Small SiPM"
        elif "Large" in part: sizename = "Large SiPM"
        if "phi,36," in part: sizename += ", iphi in [36,37]" 
        elif "phi,18," in part: sizename += ", iphi in [18,19]" 
        elif "phi,1," in part: sizename += ", iphi in [72,1]" 
        elif "HBP14RM1" in part: sizename += ", HBP14 RM1" 
        elif "HBM09RM3" in part: sizename += ", HBM09 RM3" 
        elif "HBM04RM3" in part: sizename += ", HBM04 RM3"
        elif "HBM12RM3" in part: sizename += ", HBM12 RM3"
      if subdet=="HO":
        if "HO0" in part: sizename = "0"
        elif "HO1" in part: sizename = "1"
        elif "HO2" in part: sizename = "2"
      label = subdet + " " + sizename + ""
      legend[-1].AddEntry(gr[part][meanrms], label, "pl")
    # Vertical lines at 1st of every month
    if dowhat=="daysince":
      monthlines = []
      for linehere in [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]:
        linehere = linehere - 95 # Start counting from 6th April instead of 1st January
        if lowedge > linehere or upedge < linehere: continue
        monthlines.append(ROOT.TLine(linehere, thismin - (thismax-thismin)*0.2, linehere, thismax + (thismax-thismin)*0.3))
        monthlines[-1].SetLineStyle(3)
        monthlines[-1].Draw("SAME")
    legend[-1].Draw()
    c[-1].Draw()
    c[-1].SaveAs(output+title.replace(" ", "_")+"_"+unit+".png")
    c[-1].SaveAs(output+title.replace(" ", "_")+"_"+unit+".pdf")
    c[-1].SaveAs(output+title.replace(" ", "_")+"_"+unit+".root")

if dowhat=="wholerun": exit()

##### Prepare runs for histograms
if runstoplot!=[]:
  runs = runstoplot
else:
  allruns = []
  for name in fin.GetListOfKeys():
    name = name.GetName()
    if "run" in name:
      run = name.split("run")[1]
      if run not in allruns:
        allruns.append(run)
  allruns.sort()
  ## Select only 4 runs: First, middle, last
  if False:
    runs = [allruns[0]]
    if len(allruns)>3:
      runs.append(allruns[int(len(allruns)/3)])
      runs.append(allruns[int(len(allruns)/3*2)])
    elif len(allruns)>2:
      runs.append(allruns[int(len(allruns)/2)])
    if len(allruns)>1: runs.append(allruns[-1])
  ## Or do all runs
  if False:
    runs = allruns
  ## Or do most recent ones:
  if True:
    step = 1
    runs = [allruns[-1]]
    runs.append(allruns[-1-step])
    runs.append(allruns[-1-2*step])
    runs.append(allruns[-1-3*step])


##### Collect histogram data
h = {}
hdepth = {}
hphi = {}
maxlimit = {}
sizes = ["Small", "Large"]
for unit in ["ADC", "FC"]:
 for subdet in ["HB", "HE"]:
  h[unit+subdet] = {}
  hdepth[unit+subdet] = {}
  hphi[unit+subdet] = {}

  for size in sizes:
    h[unit+subdet][size] = {}
    for alpha in ["Mean", "RMS"]:
      if alpha+subdet+unit not in maxlimit: maxlimit[alpha+subdet+unit] = [0, 999, 0] # Highest y-axis value, Smallest bin with entry, Highest bin with entry
      h[unit+subdet][size][alpha] = {}
      for run in runs:
        h[unit+subdet][size][alpha][run] = fin.Get(subdet+"_sipm"+size+"_ped"+unit+alpha+"_run"+run)
        print(subdet+"_sipm"+size+"_ped"+unit+alpha+"_run"+run)
        maxval = h[unit+subdet][size][alpha][run].GetMaximum()
        leftbin = h[unit+subdet][size][alpha][run].GetBinCenter(h[unit+subdet][size][alpha][run].FindFirstBinAbove(0))
        rightbin = h[unit+subdet][size][alpha][run].GetBinCenter(h[unit+subdet][size][alpha][run].FindLastBinAbove(0))
        if maxlimit[alpha+subdet+unit][0] < maxval: maxlimit[alpha+subdet+unit][0] = maxval
        if maxlimit[alpha+subdet+unit][1] > leftbin: maxlimit[alpha+subdet+unit][1] = leftbin
        if maxlimit[alpha+subdet+unit][2] < rightbin: maxlimit[alpha+subdet+unit][2] = rightbin
  for size in sizes: 
    for alpha in ["Mean", "RMS"]:
      if unit=="ADC":
        rebin = int((maxlimit[alpha+subdet+unit][2]-maxlimit[alpha+subdet+unit][1])*30/50) # Default 30 bin per ADC count. Rebin to ~50 total
      else:
        rebin = int((maxlimit[alpha+subdet+unit][2]-maxlimit[alpha+subdet+unit][1])*10/50) # Default 10 bin per 1 fC. Rebin to ~50 total
      if rebin > 1:
        if size==sizes[0]: maxlimit[alpha+subdet+unit][0] = maxlimit[alpha+subdet+unit][0] * rebin
        for run in runs:
          h[unit+subdet][size][alpha][run].Rebin(rebin)
      h[unit+subdet][size][alpha][runs[-1]].GetXaxis().SetRangeUser(maxlimit[alpha+subdet+unit][1], maxlimit[alpha+subdet+unit][2])
      h[unit+subdet][size][alpha][runs[-1]].GetYaxis().SetRangeUser(0, maxlimit[alpha+subdet+unit][0]*1.3)

  depths = [1, 2, 3, 4, 5, 6, 7] if subdet=="HE" else [1, 2, 3, 4]
  for depth in depths:
    hdepth[unit+subdet][depth] = {}
    for alpha in ["Mean", "RMS"]:
      if "depth"+alpha+subdet+unit not in maxlimit: maxlimit["depth"+alpha+subdet+unit] = [0, 999, 0]
      hdepth[unit+subdet][depth][alpha] = {}
      for run in runs:
        hdepth[unit+subdet][depth][alpha][run] = fin.Get(subdet+"_depth"+str(depth)+"_ped"+unit+alpha+"_run"+run)
        maxval = hdepth[unit+subdet][depth][alpha][run].GetMaximum()
        leftbin = hdepth[unit+subdet][depth][alpha][run].GetBinCenter(hdepth[unit+subdet][depth][alpha][run].FindFirstBinAbove(0))
        rightbin = hdepth[unit+subdet][depth][alpha][run].GetBinCenter(hdepth[unit+subdet][depth][alpha][run].FindLastBinAbove(0))
        if maxlimit["depth"+alpha+subdet+unit][0] < maxval: maxlimit["depth"+alpha+subdet+unit][0] = maxval
        if maxlimit["depth"+alpha+subdet+unit][1] > leftbin: maxlimit["depth"+alpha+subdet+unit][1] = leftbin
        if maxlimit["depth"+alpha+subdet+unit][2] < rightbin: maxlimit["depth"+alpha+subdet+unit][2] = rightbin
  for depth in depths:
    for alpha in ["Mean", "RMS"]:
      if unit=="ADC":
        rebin = int((maxlimit["depth"+alpha+subdet+unit][2]-maxlimit["depth"+alpha+subdet+unit][1])*30/50)
      else:
        rebin = int((maxlimit["depth"+alpha+subdet+unit][2]-maxlimit["depth"+alpha+subdet+unit][1])*10/50)
      if rebin > 1:
        if depth==depths[0]: maxlimit["depth"+alpha+subdet+unit][0] = maxlimit["depth"+alpha+subdet+unit][0] * rebin
        for run in runs:
          hdepth[unit+subdet][depth][alpha][run].Rebin(rebin)
      hdepth[unit+subdet][depth][alpha][runs[-1]].GetXaxis().SetRangeUser(maxlimit["depth"+alpha+subdet+unit][1], maxlimit["depth"+alpha+subdet+unit][2])
      hdepth[unit+subdet][depth][alpha][runs[-1]].GetYaxis().SetRangeUser(0, maxlimit["depth"+alpha+subdet+unit][0]*1.3)

  for size in sizes:
    hphi[unit+subdet][size] = {}
    for phi in [",36,37", ",18,19"]: # horizonal and vertical
      hphi[unit+subdet][size][phi] = {}
      for alpha in ["Mean", "RMS"]:
        if "phi"+alpha+subdet not in maxlimit: maxlimit["phi"+alpha+subdet+unit] = [0, 999, 0]
        hphi[unit+subdet][size][phi][alpha] = {}
        for run in runs:
          hphi[unit+subdet][size][phi][alpha][run] = fin.Get(subdet+"_sipm"+size+"_phi"+phi+"_ped"+unit+alpha+"_run"+run)
          maxval = hphi[unit+subdet][size][phi][alpha][run].GetMaximum()
          leftbin = hphi[unit+subdet][size][phi][alpha][run].GetBinCenter(hphi[unit+subdet][size][phi][alpha][run].FindFirstBinAbove(0))
          rightbin = hphi[unit+subdet][size][phi][alpha][run].GetBinCenter(hphi[unit+subdet][size][phi][alpha][run].FindLastBinAbove(0))
          if maxlimit["phi"+alpha+subdet+unit][0] < maxval: maxlimit["phi"+alpha+subdet+unit][0] = maxval
          if maxlimit["phi"+alpha+subdet+unit][1] > leftbin: maxlimit["phi"+alpha+subdet+unit][1] = leftbin
          if maxlimit["phi"+alpha+subdet+unit][2] < rightbin: maxlimit["phi"+alpha+subdet+unit][2] = rightbin
  for size in sizes:
    for phi in [",36,37", ",18,19"]:
      for alpha in ["Mean", "RMS"]:
        if unit=="ADC":
          rebin = int((maxlimit["phi"+alpha+subdet+unit][2]-maxlimit["phi"+alpha+subdet+unit][1])*30/50)
        else:
          rebin = int((maxlimit["phi"+alpha+subdet+unit][2]-maxlimit["phi"+alpha+subdet+unit][1])*10/50)
        if rebin > 1:
          if size==sizes[0] and phi==",36,37": maxlimit["phi"+alpha+subdet+unit][0] = maxlimit["phi"+alpha+subdet+unit][0] * rebin
          for run in runs:
            hphi[unit+subdet][size][phi][alpha][run].Rebin(rebin)
        hphi[unit+subdet][size][phi][alpha][runs[-1]].GetXaxis().SetRangeUser(maxlimit["phi"+alpha+subdet+unit][1], maxlimit["phi"+alpha+subdet+unit][2])
        hphi[unit+subdet][size][phi][alpha][runs[-1]].GetYaxis().SetRangeUser(0, maxlimit["phi"+alpha+subdet+unit][0]*1.3)

for unit in ["ADC", "FC"]:
 for alpha in ["Mean", "RMS"]:
  c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 800, 800 ))
  c[-1].Divide(2,2)

  ##### Draw histograms per SiPM size
  i=1
  for subdet in ["HE", "HB"]:
    for size in sizes:
      c[-1].cd(i)
      for j,run in enumerate(reversed(runs)):
        h[unit+subdet][size][alpha][run].SetLineColor(j+1)
        label = subdet + " " + size + " SiPM Pedestal "+alpha
        if j==0:
          h[unit+subdet][size][alpha][run].GetXaxis().SetTitle("Pedestal "+alpha+" (QIE11 ADC)")
          h[unit+subdet][size][alpha][run].SetTitle(label)
          h[unit+subdet][size][alpha][run].Draw()
        else:
          h[unit+subdet][size][alpha][run].Draw("same")
      legend.append(ROOT.TLegend(0.1,0.8,0.9,0.9))
      legend[-1].SetNColumns(2)
      for run in runs:
        legend[-1].AddEntry(h[unit+subdet][size][alpha][run],"Run from "+GetDay(run)+", Mean={:.3f}".format(h[unit+subdet][size][alpha][run].GetMean()),"l")
      legend[-1].Draw()
      i += 1
  c[-1].Draw()
  c[-1].SaveAs(output+"PedestalPerSize_"+alpha+"_"+unit+".png")
  c[-1].SaveAs(output+"PedestalPerSize_"+alpha+"_"+unit+".pdf")

  c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 800, 800 ))
  c[-1].Divide(2,2)


  ##### Draw histograms per depth
  for subdet in ["HE", "HB"]:
    if subdet=="HE":
      c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 1600, 800 ))
      c[-1].Divide(4,2)
    else:
      c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 800, 800 ))
      c[-1].Divide(2,2)
    i=1
    for depth in [1, 2, 3, 4, 5, 6, 7]:
      if subdet=="HB" and depth>4: continue
      c[-1].cd(i)
      for j,run in enumerate(reversed(runs)):
        hdepth[unit+subdet][depth][alpha][run].SetLineColor(j+1)
        label = subdet + " depth " + str(depth) + " Pedestal "+alpha
        if j==0:
          if unit=="ADC":
            hdepth[unit+subdet][depth][alpha][run].GetXaxis().SetTitle("Pedestal "+alpha+" (QIE11 ADC)")
          else:
            hdepth[unit+subdet][depth][alpha][run].GetXaxis().SetTitle("Pedestal "+alpha+" (fC)")
          hdepth[unit+subdet][depth][alpha][run].SetTitle(label)
          hdepth[unit+subdet][depth][alpha][run].Draw()
        else:
          hdepth[unit+subdet][depth][alpha][run].Draw("same")
      legend.append(ROOT.TLegend(0.1,0.8,0.9,0.9))
      legend[-1].SetNColumns(2)
      for run in runs:
        legend[-1].AddEntry(hdepth[unit+subdet][depth][alpha][run],"Run from "+GetDay(run)+", Mean={:.3f}".format(hdepth[unit+subdet][depth][alpha][run].GetMean()),"l")
      legend[-1].Draw()
      i += 1
    c[-1].Draw()
    c[-1].SaveAs(output+"PedestalPerDepth_"+alpha+"_"+subdet+"_"+unit+".png")
    c[-1].SaveAs(output+"PedestalPerDepth_"+alpha+"_"+subdet+"_"+unit+".pdf")

  ##### Draw histograms per phi
  for subdet in ["HE", "HB"]:
    c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 800, 800 ))
    c[-1].Divide(2,2)
    i=1
    for size in sizes:
      for phi in [",36,37", ",18,19"]:
        c[-1].cd(i)
        for j,run in enumerate(reversed(runs)):
          hphi[unit+subdet][size][phi][alpha][run].SetLineColor(j+1)
          phirange = "for iphi in [36,37] " if "36" in phi else "for iphi in [18,19] "
          label = subdet + " " + size + " SiPM Pedestal " + phirange +alpha
          if j==0:
            if unit=="ADC":
              hphi[unit+subdet][size][phi][alpha][run].GetXaxis().SetTitle("Pedestal "+alpha+" (QIE11 ADC)")
            else:
              hphi[unit+subdet][size][phi][alpha][run].GetXaxis().SetTitle("Pedestal "+alpha+" (fC)")
            hphi[unit+subdet][size][phi][alpha][run].SetTitle(label)
            hphi[unit+subdet][size][phi][alpha][run].Draw()
          else:
            hphi[unit+subdet][size][phi][alpha][run].Draw("same")
        legend.append(ROOT.TLegend(0.1,0.8,0.9,0.9))
        legend[-1].SetNColumns(2)
        for run in runs:
          legend[-1].AddEntry(hphi[unit+subdet][size][phi][alpha][run],"Run from "+GetDay(run)+", Mean={:.3f}".format(hphi[unit+subdet][size][phi][alpha][run].GetMean()),"l")
        legend[-1].Draw()
        i += 1
    c[-1].Draw()
    c[-1].SaveAs(output+"PedestalPerPhi_"+alpha+"_"+subdet+"_"+unit+".png")
    c[-1].SaveAs(output+"PedestalPerPhi_"+alpha+"_"+subdet+"_"+unit+".pdf")

# Extrapolation plots (makes more sense for lumi)
if dowhat=="lumi" and False: # Disabled: Need to revisit for 2023
  exhists = []
  for trend in ["HB_sipmLarge", "HB_sipmSmall", "HE_sipmLarge", "HE_sipmSmall", "HF", "HO", "HB_sipmLarge_phi,1,72", "HB_sipmLarge_phi,36,37"]:
    exhists.append(None)
    exhists[-1], exhistserror = MakeExtrapolation(gr, trend)
    maxx = 1.5*exhists[-1].GetPointX(exhists[-1].GetN()-1)
    #fit = ROOT.TF1( 'fit', "[0]+[1]*x+[2]*x*x", exhists[-1].GetPointX(0), exhists[-1].GetPointX(exhists[-1].GetN()-1))
    fit = ROOT.TF1( 'fit', "[0]+[1]*x", exhists[-1].GetPointX(0), maxx)
    #fit = ROOT.TF1( 'fit', "[0]+[1]*x^[2]", exhists[-1].GetPointX(0), maxx)
    #fit.SetParameter(2,1.0)
    exhistserror.Fit("fit", "F")

    if "HB" in trend: color = ROOT.kBlue
    elif "HE" in trend: color = ROOT.kGreen
    elif "HF" in trend: color = ROOT.kRed
    elif "HO" in trend: color = ROOT.kBlack
    exhists[-1].SetLineColor(color)
    exhists[-1].SetLineStyle(1)
    exhists[-1].SetMarkerStyle(21)
    exhists[-1].SetMarkerColor(color)
    exhists[-1].SetTitle("Extrapolation for "+trend)
    exhists[-1].GetXaxis().SetTitle(xtitle)
    exhists[-1].GetXaxis().SetDecimals()
    exhists[-1].GetXaxis().SetLimits(exhists[-1].GetPointX(0), maxx)
    if "HF" in trend: ytitle = "ADC (QIE10)"
    elif "HO" in trend: ytitle = "ADC (QIE8)"
    else: ytitle = "ADC (QIE11)"
    exhists[-1].GetYaxis().SetTitle(ytitle)
    thismin = ROOT.TMath.MinElement(exhists[-1].GetN(), exhists[-1].GetY())
    thismax = max(ROOT.TMath.MaxElement(exhists[-1].GetN(), exhists[-1].GetY()), fit.Eval(maxx))
    exhists[-1].SetMinimum(thismin - (thismax-thismin)*0.2)
    exhists[-1].SetMaximum(thismax + (thismax-thismin)*0.3)

    c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 600, 600 ))
    c[-1].cd()
    exhists[-1].Draw()
    c[-1].Draw()
    fit.Draw("SAME")
    legend.append(ROOT.TLegend(0.1,0.8,0.9,0.9))
    legend[-1].AddEntry(exhists[-1],"#mu_{#mu} + 2*#mu_{#sigma} + 2*#sigma_{#mu} + 2*#sigma_{#sigma}","pl")
    legend[-1].AddEntry(fit,"Linear fit (weighted towards recent data)","l")
    legend[-1].Draw()

    # Now draw hori/vert lines at every ADC count beyond current measurments
    lines = []
    for alpha in range(int(exhists[-1].GetPointY(exhists[-1].GetN()-1))+1, int(fit.Eval(maxx))+1):
      XatY = fit.GetX(alpha)
      lines.append(ROOT.TLine(exhists[-1].GetPointX(0), alpha, XatY, alpha))
      lines.append(ROOT.TLine(XatY, thismin - (thismax-thismin)*0.2, XatY, alpha))
      lines[-2].SetLineColor(ROOT.kRed)
      lines[-1].SetLineColor(ROOT.kRed)
      lines[-2].Draw("SAME")
      lines[-1].Draw("SAME")

    c[-1].SaveAs(output+"Extrapolation_"+trend+".png")
    c[-1].SaveAs(output+"Extrapolation_"+trend+".pdf")
    del exhistserror
    del fit


    ## Fit after translating ADC to FC
    #exhists.append(None)
    temphist, temphisterror = MakeChargeExtrapolation(gr, trend)
    maxx = 1.5*exhists[-1].GetPointX(exhists[-1].GetN()-1)
    fitfc = ROOT.TF1( 'fitfc', "[0]+[1]*x", exhists[-1].GetPointX(0), maxx)
    temphisterror.Fit("fitfc", "F")
    fit = ROOT.TF1( 'fit', "fc2adc_fit(fitfc(x))", exhists[-1].GetPointX(0), maxx)
    fit.SetParameter(0,fitfc.GetParameter(0))
    fit.SetParameter(1,fitfc.GetParameter(1))
    print(fitfc.Eval(20), fc2adc_fit.Eval(41), fc2adc_graph.Eval(41), fc2adc_fit.Eval(fitfc.Eval(20)), fit.Eval(20), fc2adc_graph.Eval(adc2fc_graph.Eval(12.5)))

    c.append(ROOT.TCanvas( 'c'+str(len(c)+1), 'c'+str(len(c)+1), 600, 600 ))
    c[-1].cd()
    exhists[-1].Draw()
    c[-1].Draw()
    fit.Draw("SAME")
    legend.append(ROOT.TLegend(0.1,0.8,0.9,0.9))
    legend[-1].AddEntry(exhists[-1],"#mu_{#mu} + 2*#mu_{#sigma} + 2*#sigma_{#mu} + 2*#sigma_{#sigma}","pl")
    legend[-1].AddEntry(fit,"Linear fit (weighted towards recent data)","l")
    legend[-1].Draw()

    # Now draw hori/vert lines at every ADC count beyond current measurments
    lines = []
    for alpha in range(int(exhists[-1].GetPointY(exhists[-1].GetN()-1))+1, int(fit.Eval(maxx))+1):
      XatY = fit.GetX(alpha)
      lines.append(ROOT.TLine(exhists[-1].GetPointX(0), alpha, XatY, alpha))
      lines.append(ROOT.TLine(XatY, thismin - (thismax-thismin)*0.2, XatY, alpha))
      lines[-2].SetLineColor(ROOT.kRed)
      lines[-1].SetLineColor(ROOT.kRed)
      lines[-2].Draw("SAME")
      lines[-1].Draw("SAME")

    c[-1].SaveAs(output+"ExtrapolationFC_"+trend+".png")
    c[-1].SaveAs(output+"ExtrapolationFC_"+trend+".pdf")
    del temphist
    del temphisterror
    del fit

exit()
