import os, sys, time
import numpy
import ROOT
import argparse

parser = argparse.ArgumentParser(description = 'options')

parser.add_argument('-i',
                    type = str,
                    dest = 'FileIN',
                    default = None,
                    #nargs = '+',
                    help = 'input root files')

parser.add_argument('-p',
                    action = 'store_true',
                    dest = 'isFigOut',
                    help = 'Figure file is created')

args = parser.parse_args()

FileIN = args.FileIN
isFigOut = args.isFigOut

if(FileIN == None):
    sys.exit()
    pass

DataArray = numpy.loadtxt(FileIN, unpack = True)

#draw histgram
c1 = ROOT.TCanvas('c1', 'c1', 0, 0, 1067, 750)

ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetTitleFont(132, '')
ROOT.gStyle.SetTitleFont(132, 'XYZ')
ROOT.gStyle.SetLabelFont(132, '')
ROOT.gStyle.SetLabelFont(132, 'XYZ')

c1.SetFillColor(0)
c1.SetGridx()
c1.SetGridy()
#c1.SetLogy()

MinADC = 0.0
MaxADC = 4096.0
ADCBin = 32.0

NofADCBin = int((MaxADC - MinADC)/ADCBin)

hADC = ROOT.TH1D('hADC', 'ADC', NofADCBin, MinADC, MaxADC)

for i in xrange(len(DataArray[2])):
    hADC.Fill(DataArray[2][i])
    pass

hADC.GetXaxis().SetTitle('ADC [ch]')
hADC.GetXaxis().SetTitleFont(132)
hADC.GetXaxis().SetTitleOffset(1.1)
hADC.GetXaxis().SetLabelFont(132)
hADC.GetYaxis().SetTitle('events/bin')
hADC.GetYaxis().SetTitleFont(132)
hADC.GetYaxis().SetTitleOffset(1.3)
hADC.GetYaxis().SetLabelFont(132)

hADC.SetLineColor(2)
hADC.SetLineWidth(3)
hADC.SetMarkerColor(2)
hADC.SetMarkerSize(.8)

hADC.Draw('')

c1.Update()
