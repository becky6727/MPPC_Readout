import sitcpy
from sitcpy import rbcp, to_bytes, to_bytearray
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler
import struct
import time

#-------------------------------------------------
# class for UDP control paramters
# ver1.0 2019/07/30 Y.Kibe
#-------------------------------------------------

logger = getLogger('DAQ log').getChild('SetUDPCtrl')

#global constants
HVC_1 = 483.183
HVC_2 = 780.0
ADC2HV = 2.08e-3
ADC2uA = 0.034
ADC2V = 6.85e-5
ADC2K = 4500.0

#address for start/stop DAC
addr_Rate = 0x12 #set rate of ADC
addr_end = 0x1f #set stop DAC control
addr_start = 0x1e #set start DAC control

#MUX list
tmp1 = [i for i in xrange(199, 191, -1)]
tmp2 = [i for i in xrange(207, 199, -1)]
tmp3 = [i for i in xrange(55, 47, -1)]
tmp4 = [i for i in xrange(63, 55, -1)]
tmpL = [z for sublist in [[x, y] for x, y in zip(tmp1, tmp2)] for z in sublist]
tmpH = [z for sublist in [[x, y] for x, y in zip(tmp3, tmp4)] for z in sublist]
MUXList = tmpL + tmpH + [0]

class SetUDPCtrl:

    def __init__(self, ip, port, timeout = 1000.0):

        self.timeout = timeout #1000msec -> 1sec
        self.ip = ip
        self.port = port

        #rbcp class for UDP socket
        self.rbcp = rbcp.Rbcp(self.ip, self.port, self.timeout)

        print ('connect UDP with address: %s, port: %d' %(self.ip, self.port))

        isInitialize = self.Initialize()

        pass

    def Initialize(self):

        #wait 0.2sec
        time.sleep(0.2)

        #registers
        RateADC = struct.pack('!B', 248) #50Hz
        End_Control = struct.pack('!B', 0)

        #send signal to FPGA
        set_ADC_Rate = self.rbcp.write(addr_Rate, RateADC)
        End_DAC_Control = self.rbcp.write(addr_end, End_Control)

        print 'set ADC rate and initializing....finish'
        return 0
        
    def SetHVDAC(self, HV):

        #address for FPGA register
        addr_higher = 0x10
        addr_lower = 0x11
        
        #change data to bytes
        HVDAC = int(HVC_1* HV + HVC_2)

        #bit operation
        Higher_HVDAC = struct.pack('!B', (HVDAC >> 8))
        Lower_HVDAC = struct.pack('!B', (HVDAC & 255))
        
        #write data
        higher_rbcp = self.rbcp.write(addr_higher, Higher_HVDAC)
        lower_rbcp = self.rbcp.write(addr_lower, Lower_HVDAC)
        
        #start dac control
        DAC_Control = struct.pack('!B', 1)
        
        start_DAC = self.rbcp.write(addr_start, DAC_Control)
        
        return 0

    def ReadMADC(self, data):

        #set ADC channel to FPGA register
        addr_reg1 = 0x12
        reg1 = struct.pack('!B', int(data))

        reg1_rbcp = self.rbcp.write(addr_reg1, reg1)

        #wait ADC channel change
        time.sleep(0.2)

        addr_reg2 = 0x1f
        reg2 = struct.pack('!B', 1)

        reg2_rbcp = self.rbcp.write(addr_reg2, reg2)

        #start read ADC
        addr_reg3 = addr_reg1
        reg3 = struct.pack('!B', 240)

        reg3_rbcp = self.rbcp.write(addr_reg3, reg3)

        addr_reg4 = addr_reg2
        reg4 = struct.pack('!B', 0)

        reg4_rbcp = self.rbcp.write(addr_reg4, reg4)

        #read data from ADC
        rd_data1 = 0
        rd_data2 = 0
        
        addr_rd1 = 0x4
        addr_rd2 = 0x5
        length_rd = 255

        rd_data1 = self.rbcp.read(addr_rd1, length_rd)
        rd_data2 = self.rbcp.read(addr_rd2, length_rd)

        return (rd_data1* 256) + rd_data2
    
    def MonitorHVStatus(self):

        #bias voltage and current
        BiasV = 0.0
        BiasI = 0.0

        V_ADC = self.ReadMADC(3)
        I_ADC = self.ReadMADC(4)

        BiasV = ADC2HV* V_ADC
        BiasI = ADC2uA* I_ADC

        return (BiasV, BiasI)
    
    def MonitorTemp(self):

        #temperature of Chip-A,B
        TempA = 0.0
        TempB = 0.0
        
        TempA_ADC = self.ReadMADC(5)
        TempB_ADC = self.ReadMADC(0)

        TempA = (ADC2K* ((TempA_ADC >> 16)/2.4)) - 273.0 #degreeC
        TempB = (ADC2K* ((TempB_ADC >> 16)/2.4)) - 273.0 #degreeC

        return (TempA, TempB)

    def ScanInputDAC(self):
                
        #initialize
        DAC_V_A = []
        DAC_V_B = []
        DAC_Bias_A = []
        DAC_Bias_B = []
        
        #get bias voltage
        V_ADC = self.ReadMADC(3)
        BiasV = ADC2HV* V_ADC

        #address for MUX register
        addr_MUX = 0x13
        
        for i in xrange(0, 33):
            
            MUXData = struct.pack('!B', int(MUXList[i]))
            MUX_Reg = self.rbcp.write(addr_MUX, MUXData)

            time.sleep(2.0e-3)

            if(i == 32):
                break

            #chip-A
            rd_ADC = self.ReadMADC(1)
            rd_ADC = ADC2V* rd_ADC

            DAC_V_A.append(rd_ADC)
            DAC_Bias_A.append(BiasV - rd_ADC)

            #chip-B
            rd_ADC = self.ReadMADC(2)
            rd_ADC = ADC2V* rd_ADC

            DAC_V_B.append(rd_ADC)
            DAC_Bias_B.append(BiasV - rd_ADC)

            pass
        
        return (DAC_V_A, DAC_V_B, DAC_Bias_A, DAC_Bias_B)

    def Finalize(self):

        #shutdown HV
        addr_higher = 0x10
        addr_lower = 0x11

        reg_shutdown = struct.pack('!B', 0)
        reg_start = struct.pack('!B', 1)
        
        ishigher = self.rbcp.write(addr_higher, reg_shutdown)
        islower = self.rbcp.write(addr_lower, reg_shutdown)
        isStart = self.rbcp.write(addr_start, reg_start)

        print 'shutdown DAC HV'
        
        #close socket of UDP
        del self.rbcp

        print 'delete rbcp connection'

        return 0
        
