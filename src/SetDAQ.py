import src.SocketTCP as SocketTCP
import src.TransferDataFormat as TransferDataFormat
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler
import struct
import time
from tqdm import tqdm

#-------------------------------------------------
# class for DAQ mode selection and data transfer
# ver1.0 2019/07/22 Y.Kibe
#-------------------------------------------------

logger = getLogger('DAQ log').getChild('SetDAQ')
#logger.setLevel(logging.DEBUG)

#header for writing data
HeaderW = 0x80
HeaderStart = 0x20
HeaderStop = 0x10

#address for analog output channel setting
Addr_DAQ = 0x1f
Addr_DataTake = 0x64

#register for DAQ mode
DAQMode = 0x14

#for data transfer
TransferTCP = TransferDataFormat.TransferDataFormat()

class SetDAQ:

    def __init__(self, sock):
        self.sock = SocketTCP.SocketTCP(sock)
        pass

    def RunDAQMode(self):
        Sig_DAQMode = TransferTCP.PackTCP(HeaderW, Addr_DAQ, DAQMode)
        
        Nsnt = self.sock.SendTCP(Sig_DAQMode)
        Recv_Sig_DAQMode = self.sock.RecvTCP(Nsnt)
        
        if(Sig_DAQMode and Recv_Sig_DAQMode):
            logger.info('Set Slow Control Mode')
            #print 'Set DAQ Select Mode'
        else:
            logger.error('failure to send DAQ Select Mode!!')
            return -1

        return 0

    def SelectDAQ(self, mode):

        if(mode == 1):
            Type_DAQ = 'ADC only'
        elif(mode == 2):
            Type_DAQ = 'TDC only'
        elif(mode == 3):
            Type_DAQ = 'ADC and TDC'
        else:
            logger.error('DAQ mode should be 1, 2 or 3')
            logger.error('please confirm the number of DAQ mode selection')
            return -1
        
        Sig_ModeSelect = TransferTCP.PackTCP(HeaderW, Addr_DAQ, mode)
        
        Nsnt = self.sock.SendTCP(Sig_ModeSelect)
        Recv_Sig_ModeSelect = self.sock.RecvTCP(Nsnt)
        
        if(Sig_ModeSelect and Recv_Sig_ModeSelect):
            #logger.info('Set Slow Control Mode')
            print 'Select DAQ Mode: %s' %(Type_DAQ)
        else:
            logger.error('failure to send select DAQ signal!!')
            return -1
        
        return 0
    
    def TransferDataFromDevice(self, NofData = 0):

        #error occurs if number of data is not defined
        if(NofData <= 0):
            logger.error('Number of data to be taken is not defined!!')
            return -1
        
        #initialize variable
        DataArray = [[] for i in xrange(4)]
        
        #send signal to start data taking
        Sig_DataTake = TransferTCP.PackTCP(HeaderW, Addr_DataTake, 0)
        
        Nsnt = self.sock.SendTCP(Sig_DataTake)
        Recv_Sig_DataTake = self.sock.RecvTCP(Nsnt)
        
        if(Sig_DataTake and Recv_Sig_DataTake):
            print 'Start data taking......'
        else:
            logger.error('failure to send start daq signal!!')
            return -1
        
        isErr = False
        Nnow = 0
        pbar = tqdm(total = int(1.005* NofData))
        pbar.set_description('Progress of data taking')
        
        try:
            #data taking
            while(Nnow < NofData):

                #read data from device
                tmpArray = self.ReadADC()
                
                if(tmpArray == None):
                    isErr = True
                    raise RuntimeError
                
                #fill read data into arrays
                for i in xrange(len(DataArray)):
                    DataArray[i] += tmpArray[i]
                    pass
                
                Nnow += len(tmpArray[0])
                pbar.update(len(tmpArray[0]))
                
        except KeyboardInterrupt:
            
            logger.info('keyborad interrupt(ctrl-c) is detected!!')
            print 'stop data taking by ctrl-c'
            return self.StopADC()            

        pbar.close()
        
        if(isErr):
            logger.error('error in read data!!')
            return -1

        print 'Finish to transfer data!!'

        return DataArray
        
    def ReadADC(self):

        #set variables
        ChipArray = []
        ChArray = []
        ADCArray = []
        OFArray = [] #overflow flags
        
        #header of data
        headerADC = self._adc_header()
        
        RecvHeader = self.sock.RecvTCP(len(headerADC))
        RecvHeader = struct.unpack('3L', RecvHeader)

        #check abnormal header
        if(RecvHeader[0] != 0xffffea0c):
            logger.error('abnormal header from data transfer!!')
            print format(RecvHeader[0], '08x')
            raise RuntimeError
        
        #get information from recieved header
        NofWord = (RecvHeader[1] & 0xffff) #slice lower 16bit

        RecvData = self.sock.RecvTCP(4* NofWord)
        RecvData = struct.unpack('%dL' %(NofWord), RecvData)
        
        #analyze data
        for i in xrange(len(RecvData)):
            ChipAB = ((RecvData[i] & 0xff000000) >> 24) #higher 8bit bitmask and bitshift
            ChMPPC = (((RecvData[i] & 0x00ff0000) >> 16) & 0x1f)
            ADC = (RecvData[i] & 0x00000fff) 
            isOverflow = ((RecvData[i] & 0x00001fff) >> 12)

            #fill variables into arrays
            ChipArray.append(ChipAB)
            ChArray.append(ChMPPC)
            ADCArray.append(ADC)
            OFArray.append(isOverflow)
            
            pass

        return (ChipArray, ChArray, ADCArray, OFArray)
    
    def _adc_header(self, header1 = 1, header2 = 1, header3 = 1):
        ret = struct.pack('3L',
                          header1,
                          header2,
                          header3)
        return ret

    def StopADC(self):

        Sig_Stop = TransferTCP.PackTCP(HeaderStop, Addr_DataTake, 0x0)
        self.sock.SendTCP(Sig_Stop)

        time.sleep(1.0)
        
        Sig_Clear = TransferTCP.PackTCP(0x0, Addr_DataTake, 0x0)
        self.sock.SendTCP(Sig_Clear)

        time.sleep(0.1)
        
        print 'Stop ADC'

        return 0
    
