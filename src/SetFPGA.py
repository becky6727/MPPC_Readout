import src.SocketTCP as SocketTCP
import src.TransferDataFormat as TransferDataFormat
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler
import struct

#------------------------------------------
# class for initializing FPGA parameters
# ver1.0 2019/07/12 Y.Kibe
#------------------------------------------

logger = getLogger('DAQ log').getChild('SetFPGA')
#logger.setLevel(logging.DEBUG)

#header
HeaderW = 0x80

#for transfer data
TransferTCP = TransferDataFormat.TransferDataFormat()

class SetFPGA:

    def __init__(self, sock, Dict):
        self.sock = SocketTCP.SocketTCP(sock)
        self.Dict = Dict
        pass

    def SetParameter(self, ID):

        if(ID > 5):
            logger.error('Setting ID is lower than 5(0 - 4)')
            return -1

        KeyName = 'Set%d' %(ID + 1)
        ParList = self.Dict['FPGA_Setting'][KeyName]['Value']
        ParName = self.Dict['FPGA_Setting'][KeyName]['ParName']
    
        #set address to write data
        if(ID != 4):
            Addr = ID
        else:
            Addr = ID + 1
            pass
        
        #set parameters
        ParData = 0
        
        for i in xrange(len(ParList)):
            ParData = ParData + (ParList[i] << i)
            pass
        
        #bit mask
        ParData = (ParData & 255)

        #Data structure:
        #XXXXXXXX(8bit header) + XXXXXXXX(8bit address) + XXXXXXXX(8bit data) + XXXXXXXX(8bit blank)
        ParData = TransferTCP.PackTCP(HeaderW, Addr, ParData)
        
        try:
            #send data, return byte size to be sent
            Nsnt = self.sock.SendTCP(ParData)
        except RuntimeError:
            return -1
        
        try:
            #recieve data from SiTCP module to confirm
            Recv = self.sock.RecvTCP(Nsnt)
        except RuntimeError:
            return -1
        
        if(ParData != Recv):
            print struct.unpack('I', ParData), struct.unpack('I', Recv)
            raise RuntimeError('sent and recieved data does not match!')
        
        #show settings
        AddrRcv = (struct.unpack('4B', Recv)[2] & 255)
        #print 'write register to FPGA at Address: %d(%s)' %(AddrRcv, format(AddrRcv, '08b'))
        #logger.debug('write register to FPGA at Address: %d(%s)' %(AddrRcv, format(AddrRcv, '08b')))
        
        RegisterRcv = (struct.unpack('4B', Recv)[1] & 255) #bit mask and slice info at 16-9 bit
        #RegisterRcv = format(RegisterRcv, '08b') #8bit representation
        RegisterRcv = format(RegisterRcv, '02x') #hex representation
        #RegisterRcv = RegisterRcv[::-1] #reverse list

        logger.info('Send ---> Recv: %s' %(RegisterRcv))
        '''
        for i in xrange(len(RegisterRcv)):
            if(ParName[i] == 'none'):
                continue
            if(RegisterRcv[i] == '1'):
                #print '%s: ON' %(ParName[i])
                logger.info('%s: ON' %(ParName[i]))
            else:
                #print '%s: OFF' %(ParName[i])
                logger.info('%s: OFF' %(ParName[i]))
                pass
            pass
        '''
        
        return 0
        
