import src.SocketTCP as SocketTCP
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler

#------------------------------------------
# class for initializing FPGA parameters
# ver1.0 2019/07/12 Y.Kibe
#------------------------------------------

logger = getLogger('DAQ log').getChild('SetFPGA')
#logger.setLevel(logging.DEBUG)

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
    
        #set header for write-mode
        HeaderW = (128 << 24)

        #set address to write data
        if(ID != 4):
            Addr = (ID << 16)
        else:
            Addr = ((ID + 1) << 16)
            pass

        #set parameters
        ParData = 0

        for i in xrange(len(ParList)):
            ParData = ParData + (ParList[i] << i)
            pass

        #bit mask since data should be specific position(16-9bit)
        ParData = ((ParData & 255) << 8)

        #Data structure:
        #XXXXXXXX(8bit header) + XXXXXXXX(8bit address) + XXXXXXXX(8bit data) + XXXXXXXX(8bit blank)
        ParData = HeaderW + Addr + ParData 
        ParData = format(ParData, '032b')
    
        self.sock.SendTCP(ParData)

        #recieve data from SiTCP module to confirm
        Recv = self.sock.RecvTCP(len(ParData))
    
        #show settings
        AddrRcv = ((int(ParData, 2) >> 16) & 255)
        print 'write register to FPGA at Address: %d(%s)' %(AddrRcv, format(AddrRcv, '08b'))
        #logger.debug('write register to FPGA at Address: %d(%s)' %(AddrRcv, format(AddrRcv, '08b')))
        
        RegisterRcv = ((int(ParData, 2) >> 8) & 255) #bit mask and slice info at 16-9 bit
        RegisterRcv = format(RegisterRcv, '08b') #8bit representation
        RegisterRcv = RegisterRcv[::-1] #reverse list
    
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
    
        return 0
        
