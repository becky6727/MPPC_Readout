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
        Sig_DAQMode = TransferTCP.PackTCP(HeaderW, 0x0, DAQMode)
        
        Nsnt = self.sock.SendTCP(Sig_DAQMode)
        Recv_Sig_DAQMode = self.sock.RecvTCP(Nsnt)

        #for debug
        #tmp = struct.unpack('I', Recv_Sig_DAQMode)
        #print format(tmp[0], '08x')
        
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

        #for debug
        #tmp = struct.unpack('I', Recv_Sig_ModeSelect)
        #print format(tmp[0], '08x')
        
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
        #DataArray = [[] for i in xrange(4)]
        DataArray = []
        
        #send signal to start data taking
        Sig_DataTake = TransferTCP.PackTCP(HeaderStart, Addr_DataTake, 0)

        #just only send because recv value is data
        Nsnt = self.sock.SendTCP(Sig_DataTake)
        
        #data taking
        for i in tqdm(xrange(NofData), desc = 'Data taking'):
                
            #read data from device
            try:
                tmpArray = self.ReadADC()
                DataArray.append(tmpArray)
            except RuntimeError:
                logger.info('fatal error is occrured')
                print 'stop data taking by fatal error'
                self.StopADC()
            except KeyboardInterrupt:            
                logger.info('keyborad interrupt(ctrl-c) is detected!!')
                print 'stop data taking by ctrl-c'
                self.StopADC()            

            #fill read data into arrays
            '''
            for j in xrange(len(DataArray)):
                DataArray[j] += tmpArray[j]
                pass
            '''
            
            pass                
            
        print 'Finish to transfer data!!'

        #end of adc
        self.StopADC()
        
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
        Header = struct.unpack('3I', RecvHeader)

        #for debug
        #for i in xrange(len(RecvHeader)):
        #    tmp1 = (RecvHeader[i] & 0xffff0000) >> 16
        #    tmp2 = (RecvHeader[i] & 0x0000ffff)
        #    print format(tmp1, '04x')
        #    print format(tmp2, '04x')
        #    pass
        
        #check abnormal header
        if(Header[0] != 0xffffea0c):
            logger.error('abnormal header from data transfer!!')
            print format(RecvHeader[0], '08x')
            raise RuntimeError
        
        #get information from recieved header
        #NofWord = (RecvHeader[1] & 0xffff) #slice lower 16bit
        NofWord = 64 #slice lower 16bit, now fixed to be 64 words 

        retry = 0
        
        RecvData = self.sock.RecvTCP(4* NofWord)

        '''
        RecvData = struct.unpack('%dI' %(NofWord), RecvData)
        
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
        '''
        
        #return (ChipArray, ChArray, ADCArray, OFArray)
        return bytearray(RecvHeader + RecvData)
    
    def _adc_header(self, header1 = 1, header2 = 1, header3 = 1):
        ret = struct.pack('3I',
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
    
