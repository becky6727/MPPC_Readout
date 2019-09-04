import os, sys, time, datetime
import json
import socket
import argparse
import struct
import numpy

#for progress bar
from tqdm import tqdm

#for GUI
import Tkinter as Tk
from PIL import ImageTk, Image
import tkMessageBox

#for log
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler

#class for DAQ
import src.SocketTCP as SocketTCP
import src.SetFPGA as SetFPGA
import src.SetSlowControl as SetSlowControl
import src.SetAnalogOutput as SetAnalogOutput
import src.SetDAQ as SetDAQ
import src.SetUDPCtrl as SetUDPCtrl

#misc
import sitcpy

#----------------------------------------------
# DAQ client software based on GUI by Tkinter  
# for EASIROC module
# 2019/08/14 ver2.0 Y.Kibe
#----------------------------------------------

#define widget and frame
class Application(Tk.Frame):

    def __init__(self, master = None):

        #root frame
        Tk.Frame.__init__(self, master)
        
        self.grid_columnconfigure((0, 1, 2, 3, 4), weight = 1)
        self.grid_rowconfigure((0, 1, 2, 3), weight = 1)
        self.pack(expand = 1, fill = Tk.X, anchor = Tk.NW)
        
        #frame for button
        self.FrameBtn = Tk.Frame(self)
        self.FrameBtn.configure(bg = 'black')
        #self.FrameBtn.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.X)
        self.FrameBtn.grid(row = 0, column = 0, columnspan = 5, padx = 5, pady = 5, sticky = Tk.EW)

        #frame for DAQ mode
        #self.FrameMode = Tk.Frame(self)
        self.FrameMode = Tk.LabelFrame(self, text = 'DAQ mode selection', bd = 2)
        #self.FrameMode.configure(bg = 'green')
        self.FrameMode.grid_columnconfigure((0, 1, 2, 3), weight = 1)
        self.FrameMode.grid_rowconfigure((0, 1, 2), weight = 1)
        #self.FrameMode.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.X)
        self.FrameMode.grid(row = 1, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = Tk.EW)

        #frame for run number and # of events
        #self.FrameRun = Tk.Frame(self)
        self.FrameRun = Tk.LabelFrame(self, text = 'Preset', bd = 2)
        #self.FrameRun.configure(bg = 'red')
        self.FrameRun.grid_columnconfigure((0, 1), weight = 1)
        self.FrameRun.grid_rowconfigure((0, 1), weight = 1)
        #self.FrameRun.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.X)
        self.FrameRun.grid(row = 2, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = Tk.EW)
        
        #frame for connection
        #self.FrameIP = Tk.Frame(self)
        self.FrameIP = Tk.LabelFrame(self, text = 'Connection', bd = 2)
        #self.FrameIP.configure(bg = 'blue')
        self.FrameIP.grid_columnconfigure((0, 1), weight = 1)
        self.FrameIP.grid_rowconfigure((0, 1, 2), weight = 1)
        #self.FrameIP.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.X)
        self.FrameIP.grid(row = 3, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = Tk.EW)

        #frame for HV setting
        #self.FrameHV = Tk.Frame(self)
        self.FrameHV = Tk.LabelFrame(self, text = 'HV setting', bd = 2)
        #self.FrameHV.configure(bg = 'blue')
        self.FrameHV.grid_columnconfigure((0, 1), weight = 1)
        self.FrameHV.grid_rowconfigure((0), weight = 1)
        #self.FrameHV.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.X)
        self.FrameHV.grid(row = 4, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = Tk.EW)

        #frame for monitoring HV
        self.FrameMonHV = Tk.LabelFrame(self, text = 'Monitoring HV', bd = 2)
        self.FrameMonHV.configure(bg = 'yellow')
        self.FrameMonHV.grid_columnconfigure((0, 1, 2, 3, 4), weight = 1)
        self.FrameMonHV.grid_rowconfigure((0), weight = 1)
        #self.FrameMonHV.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.BOTH)
        self.FrameMonHV.grid(row = 1, column = 2, columnspan = 3, padx = 5, pady = 5, sticky = Tk.EW)

        #frame for input DAC HV
        #self.FrameDAC = Tk.Frame(self)
        self.FrameDAC = Tk.LabelFrame(self, text = 'Input DAC HV and bias volutage, ch No.XX = DAC-HV/biasV', bd = 2)
        self.FrameDAC.configure(bg = 'yellow')
        self.FrameDAC.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), weight = 1)
        self.FrameDAC.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), weight = 1)
        #self.FrameDAC.pack(expand = 1, padx = 5, pady = 5, anchor = Tk.NW, fill = Tk.BOTH)
        self.FrameDAC.grid(row = 2, column = 2, rowspan = 3, columnspan = 3, padx = 5, pady = 5, sticky = Tk.EW)

        #flag for socket object creation
        self.isInitialize = False

        #widget creation
        self.CreateWidgets()
        
    def CreateWidgets(self):

        #button of 'Initialize'
        self.Initialize = Tk.Button(self.FrameBtn, text = 'Initialize', width = 14, command = self.InitDAQ)
        self.Initialize.pack(fill = Tk.X, expand = 1, padx = 0, side = Tk.LEFT, anchor = Tk.NW)

        #button of 'Start DAQ'
        self.StartDAQ = Tk.Button(self.FrameBtn, text = 'Start DAQ', width = 14, command = self.DoDAQ)
        self.StartDAQ.pack(fill = Tk.X, expand = 1, padx = 0, side = Tk.LEFT, anchor = Tk.NW)
        self.StartDAQ.config(state = 'disable')
        
        #button of 'Quit DAQ'
        self.QuitDAQ = Tk.Button(self.FrameBtn, text = 'Quit DAQ', width = 14, command = self.QuitDAQ)
        self.QuitDAQ.pack(fill = Tk.X, expand = 1, padx = 0, side = Tk.LEFT, anchor = Tk.NW)

        #button of 'reload SC'
        self.ReloadSC = Tk.Button(self.FrameBtn, text = 'Reload Slow Ctrl Pars', width = 14, command = self.LoadSlowCtrlPar)
        self.ReloadSC.pack(fill = Tk.X, expand = 1, padx = 0, side = Tk.LEFT, anchor = Tk.NW)
        self.ReloadSC.config(state = 'disable')

        #button of blank(for future custumize)
        self.BlankBtn3 = Tk.Button(self.FrameBtn, text = 'Blank', width = 14)
        self.BlankBtn3.pack(fill = Tk.X, expand = 1, padx = 0, side = Tk.LEFT, anchor = Tk.NW)
        
        #input field for DAQ mode
        #self.LabelMode = Tk.Label(self.FrameMode, text = 'DAQ mode selection:')
        #self.LabelMode.grid(row = 0, column = 1, sticky = Tk.EW)
        self.VarMode = Tk.IntVar()
        self.ModeADC = Tk.Radiobutton(self.FrameMode, value = 1, variable = self.VarMode, text = 'ADC only')
        self.ModeTDC = Tk.Radiobutton(self.FrameMode, value = 2, variable = self.VarMode, text = 'TDC only')
        self.ModeADCTDC = Tk.Radiobutton(self.FrameMode, value = 3, variable = self.VarMode, text = 'ADC + TDC')
        #self.HV.insert(Tk.END, '')
        self.ModeADC.grid(row = 1, column = 1, columnspan = 1, pady = 5, sticky = Tk.W)
        self.ModeTDC.grid(row = 2, column = 1, columnspan = 1, pady = 5, sticky = Tk.W)
        self.ModeADCTDC.grid(row = 3, column = 1, columnspan = 1, pady = 5, sticky = Tk.W)

        #set run number
        self.LabelRunN = Tk.Label(self.FrameRun, text = 'Run number')
        self.LabelRunN.grid(row = 0, column = 0, pady = 10, sticky = Tk.E)
        self.VarRunN = Tk.StringVar()
        self.RunN = Tk.Entry(self.FrameRun, textvariable = self.VarRunN, width = 15)
        PresetRunN = len(os.listdir('./log/'))
        self.RunN.insert(Tk.END, '%s' %(str(PresetRunN)))
        self.RunN.grid(row = 0, column = 1, pady = 10, sticky = Tk.W)

        self.LabelEventN = Tk.Label(self.FrameRun, text = 'Number of Events')
        self.LabelEventN.grid(row = 1, column = 0, pady = 10, sticky = Tk.E)
        self.VarEventN = Tk.StringVar()
        self.EventN = Tk.Entry(self.FrameRun, textvariable = self.VarEventN, width = 15)
        #self.EventN.insert(Tk.END, '')
        self.EventN.grid(row = 1, column = 1, pady = 10, sticky = Tk.W)
        
        #input field for ip address
        self.LabelIP = Tk.Label(self.FrameIP, text = 'IP address')
        self.LabelIP.grid(row = 0, column = 0, pady = 10, sticky = Tk.E)
        self.VarIP = Tk.StringVar()
        self.IPAddr = Tk.Entry(self.FrameIP, textvariable = self.VarIP, width = 15)
        #self.IPAddr.insert(Tk.END, '192.168.10.') #for test
        self.IPAddr.insert(Tk.END, '192.168.10.11') #for my module
        self.IPAddr.grid(row = 0, column = 1, pady = 10, sticky = Tk.W)

        #input field for TCP port
        self.LabelTCP = Tk.Label(self.FrameIP, text = 'TCP port')
        self.LabelTCP.grid(row = 1, column = 0, pady = 10, sticky = Tk.E)
        self.VarTCP = Tk.StringVar()
        self.PortTCP = Tk.Entry(self.FrameIP, textvariable = self.VarTCP, width = 10)
        self.PortTCP.insert(Tk.END, '24')
        self.PortTCP.grid(row = 1, column = 1, pady = 10, sticky = Tk.W)

        #input field for UDP port
        self.LabelUDP = Tk.Label(self.FrameIP, text = 'UDP port')
        self.LabelUDP.grid(row = 2, column = 0, pady = 10, sticky = Tk.E)
        self.VarUDP = Tk.StringVar()
        self.PortUDP = Tk.Entry(self.FrameIP, textvariable = self.VarUDP, width = 10)
        self.PortUDP.insert(Tk.END, '4660')
        self.PortUDP.grid(row = 2, column = 1, pady = 10, sticky = Tk.W)
        
        #input field for HV
        self.LabelHV = Tk.Label(self.FrameHV, text = 'Internal HV [V]')
        self.LabelHV.grid(row = 0, column = 0, pady = 10, sticky = Tk.E)
        self.VarHV = Tk.StringVar()
        self.HV = Tk.Entry(self.FrameHV, textvariable = self.VarHV, width = 10)
        #self.HV.insert(Tk.END, '') #for test
        self.HV.insert(Tk.END, '50') #for my module
        self.HV.grid(row = 0, column = 1, pady = 10, sticky = Tk.W)

        #output field for monitoring HV status
        self.LabelMonHV = Tk.Label(self.FrameMonHV, text = 'Bias Voltage [V]')
        self.LabelMonHV.grid(row = 0, column = 0, pady = 10, sticky = Tk.E)
        self.VarMonHV = Tk.StringVar()
        self.MonHV = Tk.Entry(self.FrameMonHV, textvariable = self.VarMonHV, width = 10)
        self.MonHV.grid(row = 0, column = 1, pady = 10, sticky = Tk.W)
        self.MonHV.configure(state = 'readonly')

        #for bias current
        self.LabelMonA = Tk.Label(self.FrameMonHV, text = 'Bias Current [uA]')
        self.LabelMonA.grid(row = 0, column = 3, pady = 10, sticky = Tk.E)
        self.VarMonA = Tk.StringVar()
        self.MonA = Tk.Entry(self.FrameMonHV, textvariable = self.VarMonA, width = 10)
        self.MonA.grid(row = 0, column = 4, pady = 10, sticky = Tk.W)
        self.MonA.configure(state = 'readonly')
        
        #output field for monitor input DAC HV
        self.LabelDAC1 = [Tk.Label(self.FrameDAC, text = 'ch No.%02d' %(i+1)) for i in xrange(64)]
        self.LabelDAC2 = [Tk.Label(self.FrameDAC, text = '/') for i in xrange(64)]
        self.VarDAC1 = [Tk.StringVar() for i in xrange(len(self.LabelDAC1))]
        self.VarDAC2 = [Tk.StringVar() for i in xrange(len(self.LabelDAC1))]
        self.DAC1 = [Tk.Entry(self.FrameDAC, textvariable = self.VarDAC1[i], width = 4) for i in xrange(len(self.VarDAC1))]
        self.DAC2 = [Tk.Entry(self.FrameDAC, textvariable = self.VarDAC2[i], width = 4) for i in xrange(len(self.VarDAC2))]

        for i in xrange(len(self.LabelDAC1)):
            if(i < 16):
                self.LabelDAC1[i].grid(row = i, column = 0, pady = 2, sticky = Tk.E)
                self.DAC1[i].grid(row = i, column = 1, pady = 1, sticky = Tk.W)
                self.LabelDAC2[i].grid(row = i, column = 2, pady = 2, sticky = Tk.W)
                self.DAC2[i].grid(row = i, column = 3, pady = 1, sticky = Tk.W)
            elif((i >= 16) and (i < 32)):
                self.LabelDAC1[i].grid(row = i - 16, column = 4, pady = 2, sticky = Tk.E)
                self.DAC1[i].grid(row = i - 16, column = 5, pady = 1, sticky = Tk.W)
                self.LabelDAC2[i].grid(row = i - 16, column = 6, pady = 2, sticky = Tk.W)
                self.DAC2[i].grid(row = i - 16, column = 7, pady = 1, sticky = Tk.W)
            elif((i >= 32) and (i < 48)):
                self.LabelDAC1[i].grid(row = i - 32, column = 8, pady = 2, sticky = Tk.E)
                self.DAC1[i].grid(row = i - 32, column = 9, pady = 1, sticky = Tk.W)
                self.LabelDAC2[i].grid(row = i - 32, column = 10, pady = 2, sticky = Tk.W)
                self.DAC2[i].grid(row = i - 32, column = 11, pady = 1, sticky = Tk.W)
            else:
                self.LabelDAC1[i].grid(row = i - 48, column = 12, pady = 2, sticky = Tk.E)
                self.DAC1[i].grid(row = i - 48, column = 13, pady = 1, sticky = Tk.W)
                self.LabelDAC2[i].grid(row = i - 48, column = 14, pady = 2, sticky = Tk.W)
                self.DAC2[i].grid(row = i - 48, column = 15, pady = 1, sticky = Tk.W)
                pass
            self.DAC1[i].configure(state = 'readonly')
            self.DAC2[i].configure(state = 'readonly')
            pass
        
        pass

    #pop up error message
    def PopError(self, Message):
        tkMessageBox.showerror('ERROR', Message, parent = self)
        self.quit()
        pass
    
    #pop up just before starting run
    def PopStart(self):
        return tkMessageBox.askokcancel('Start Run', 'Settings are valid.\n Ready to start DAQ?', parent = self)
        
    #pop up at end of run
    def PopEndRun(self):
        pass
    
    def InitDAQ(self):
        
        #check ip address
        try:
            socket.inet_aton(self.VarIP.get())
        except socket.error:
            Msg = 'invalid ip address: %s' %(self.VarIP.get())
            self.PopError(Msg)
            raise RuntimeError
        else:
            self.IPAddr = self.VarIP.get()
            pass
        
        #port no of tcp
        self.PortTCP = int(self.VarTCP.get())

        #port no of udp
        self.PortUDP = int(self.VarUDP.get())

        #internal HV setting
        try:
            self.HV = float(self.VarHV.get())
        except ValueError:
            Msg = 'Internal HV value is invald!'
            self.PopError(Msg)
            raise RuntimeError
        
        if((self.HV >= 90.0) or (self.HV <= 0.0)):
            Msg = 'Inernal HV is out of range!!'
            self.PopError(Msg)
            raise RuntimeError
        
        #daq mode selection
        self.DAQMode = int(self.VarMode.get())

        if(self.DAQMode <= 0):
            Msg = 'DAQ mode is not selected!!'
            self.PopError(Msg)
            raise RuntimeError
        
        #Run number
        self.RunNumber = int(self.VarRunN.get())

        #number of events to be measured
        try:
            self.NofEvt = int(self.VarEventN.get())
        except ValueError:
            Msg = 'Number of events is invalid!'
            self.PopError(Msg)
            raise RuntimeError
            pass

        #set logger
        self.Log(self.RunNumber)

        #time interval for timeout
        Sec = 10
        uSec = 0
        Timeval = struct.pack('ll', Sec, uSec)
        
        #socket for TCP/IP and optional settings
        self.SockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.SockTCP.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, Timeval)
        self.SockTCP.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.SockTCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        #class for safer transfer/recieving
        self.DAQSockTCP = SocketTCP.SocketTCP(self.SockTCP)
        
        #connection
        self.Sock = self.DAQSockTCP.ConnectTCP(self.IPAddr, self.PortTCP)
    
        #load configuration file
        FileConfig = './config/Settings.json'
        ConfigDict = json.load(open(FileConfig, 'r'))
        
        #misc
        print ''

        #----- initialize process with TCP -----#
        InitializeFPGA = SetFPGA.SetFPGA(self.Sock, ConfigDict)
        
        for i in tqdm(xrange(0, 5), desc = 'FPGA Setting'):
            InitializeFPGA.SetParameter(i)
            time.sleep(0.01) #wait 10usec before next step
            pass
        
        #misc
        print ''

        #wait 0.1sec before next step...
        time.sleep(0.1)
        
        #initialize Slow Control and Analog Output Channel
        InitializeSlowCtrl = SetSlowControl.SetSlowControl(self.Sock, ConfigDict)
        InitializeAnalog = SetAnalogOutput.SetAnalogOutput(self.Sock, ConfigDict)
        
        #0 is Chip-A, 1 is Chip-B
        for ChipSelect in xrange(0, 2):
            
            #initialize slow control data
            (isDoneSC, SumSC) = InitializeSlowCtrl.SetParameter(ChipSelect)
            
            if(isDoneSC < 0):
                sys.exit()
                pass
            
            #initialize analog output setting
            (isDoneAnalog, SumAnalog) = InitializeAnalog.SetParameter(ChipSelect)
            
            if(isDoneAnalog < 0):
                sys.exit()
                pass
                        
            pass
        
        #DAQ mode selection
        self.DAQCtrl = SetDAQ.SetDAQ(self.Sock)
        
        #initialize DAQ
        isRunDAQ = self.DAQCtrl.RunDAQMode()
        
        if(isRunDAQ < 0):
            sys.exit()
            pass
        
        isSelectDAQ = self.DAQCtrl.SelectDAQ(self.DAQMode)
        
        if(isSelectDAQ < 0):
            sys.exit()
            pass
        
        #----- initialize via UDP -----#
        while True:
            try:
                self.UDP = SetUDPCtrl.SetUDPCtrl(self.IPAddr, self.PortUDP)
                break
            except RbcpError:
                print 'fail to connect UDP, retry'
                time.sleep(1)
                pass
            pass

        while True:
            try:
                isHV = self.UDP.SetHVDAC(self.HV)
                break
            except RbcpError:
                time.sleep(1)
                print 'retry HV setting'
                pass
            pass
        
        #wait 1sec
        time.sleep(1.0)

        #monitor HV
        while True:
            try:
                (BiasV, BiasI) = self.UDP.MonitorHVStatus()            
                break
            except RbcpError:
                print 'Error, retry Monitor HV status'
                time.sleep(1)
                pass
            pass

        #display HV
        self.MonHV.configure(state = 'normal')
        self.MonHV.insert(Tk.END, '{:.2f}'.format(BiasV))
        self.MonHV.configure(state = 'readonly')

        #display current
        self.MonA.configure(state = 'normal')
        self.MonA.insert(Tk.END, '{:.2f}'.format(BiasI))
        self.MonA.configure(state = 'readonly')

        #misc
        print ''

        #monitor input DAC HV
        while True:
            try:
                (DAC_V_A, DAC_V_B, DAC_Bias_A, DAC_Bias_B) = self.UDP.ScanInputDAC()
                break
            except RbcpError:
                print 'Error, retry Scan Input DAC'
                time.sleep(1)
                pass
            pass

        #display input DAC HV
        for i in xrange(len(DAC_V_A)):

            self.DAC1[i].configure(state = 'normal')
            self.DAC1[i].insert(Tk.END, '{:.2f}'.format(DAC_V_A[i]))
            self.DAC1[i].configure(state = 'readonly')

            self.DAC2[i].configure(state = 'normal')
            self.DAC2[i].insert(Tk.END, '{:.2f}'.format(DAC_Bias_A[i]))
            self.DAC2[i].configure(state = 'readonly')

            pass

        for i in xrange(len(DAC_V_B)):

            self.DAC1[i + 32].configure(state = 'normal')
            self.DAC1[i + 32].insert(Tk.END, '{:.2f}'.format(DAC_V_B[i]))
            self.DAC1[i + 32].configure(state = 'readonly')

            self.DAC2[i + 32].configure(state = 'normal')
            self.DAC2[i + 32].insert(Tk.END, '{:.2f}'.format(DAC_Bias_B[i]))
            self.DAC2[i + 32].configure(state = 'readonly')

            pass

        #misc
        print ''
        
        self.isInitialize = True
        self.StartDAQ.config(state = 'active')
        self.ReloadSC.config(state = 'active')
        self.Initialize.config(state = 'disable')
        
        pass
    
    def DoDAQ(self):
                
        #--------- DAQ main ---------#
        if(self.PopStart()):
            #----- data taking -----#
            OutputFile = './Data/Run%04d.ebf' %(self.RunNo)
            DataArray = self.DAQCtrl.TransferDataFromDevice(self.NofEvt)
            
            fout = open(OutputFile, 'wb')
            for i in xrange(len(DataArray)):
                fout.write(DataArray[i])
                pass
        else:
            print 'please confirm settings'
            pass
        #-------- END DAQ -----------#
        pass

    def LoadSlowCtrlPar(self):

        #load configuration file
        FileConfig = './config/Settings.json'
        ConfigDict = json.load(open(FileConfig, 'r'))
        
        #initialize Slow Control and Analog Output Channel
        InitializeSlowCtrl = SetSlowControl.SetSlowControl(self.Sock, ConfigDict)
        InitializeAnalog = SetAnalogOutput.SetAnalogOutput(self.Sock, ConfigDict)
        
        #0 is Chip-A, 1 is Chip-B
        for ChipSelect in xrange(0, 2):
            
            #initialize slow control data
            (isDoneSC, SumSC) = InitializeSlowCtrl.SetParameter(ChipSelect)
            
            if(isDoneSC < 0):
                sys.exit()
                pass
            
            #initialize analog output setting
            (isDoneAnalog, SumAnalog) = InitializeAnalog.SetParameter(ChipSelect)
            
            if(isDoneAnalog < 0):
                sys.exit()
                pass
            
            pass

        #initialize DAQ
        isRunDAQ = self.DAQCtrl.RunDAQMode()
        
        if(isRunDAQ < 0):
            sys.exit()
            pass
        
        pass
    
    def QuitDAQ(self):
                
        #finalize process
        while(self.isInitialize):
            try:
                #finalize
                self.UDP.Finalize()
                break
            except sitcpy.rbcp.RbcpError as e:
                print 'UDP connection timeout is detected! try reconncet...'
                #reconnect
                time.sleep(1)
                self.UDP = SetUDPCtrl.SetUDPCtrl(self.IPAddr, self.PortUDP)
                pass
            pass

        if(self.isInitialize):
            self.DAQSockTCP.CloseTCP()
            self.SockTCP.close()
            pass
        
        print 'bye-bye~'
        self.quit()
        sys.exit()
        pass
    
    def Log(self, Nrun):
        
        #log file settings
        dt_now = datetime.datetime.now()
        Log = './log/Run%04d_%04d-%02d-%02d.log' %(Nrun, dt_now.year, dt_now.month, dt_now.day)
        
        logger = getLogger('DAQ log')
        logger.setLevel(logging.DEBUG)
        
        handler_format = Formatter('%(asctime)s: %(name)s, %(levelname)s, %(message)s')
        
        stream_handler = StreamHandler()
        #stream_handler.setLevel(logging.DEBUG)
        stream_handler.setLevel(logging.WARNING)
        #stream_handler.setLevel(logging.ERROR) #if want to show no info
        stream_handler.setFormatter(Formatter('%(message)s'))
        
        file_handler = FileHandler(Log, 'a')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(handler_format)
    
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        pass

#main roop
root = Tk.Tk()

#set size and title of window
root.geometry('1000x680')
root.title('eCAT, EASIROC module Controll Application Tools')

app = Application(master = root)
app.mainloop()
