import src.SocketTCP as SocketTCP
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler

#-------------------------------------------------
# class for initializing Slow Control Parameters
# ver1.0 2019/07/18 Y.Kibe
#-------------------------------------------------

logger = getLogger('DAQ log').getChild('SetSlowCtrl')

#header for writing data
HeaderW = (128 << 24)

#address for various modes
Addr_Data = (10 << 16)
Addr_SCMode = (1 << 16)
Addr_StartCycle = Addr_SCMode
Addr_LoadSC = Addr_SCMode

#register for various modes
SCMode = (240 << 8)
StartCycle = (242 << 8)
LoadSC = (241 << 8)

#paramters, do not arange the order of list!!!
ParNameList = ['NC', 'En32Trig', 'EnOR32', 'EnDigOut', 'EnLVDS', 'EnProbeOTAq', 'EnLGOTAq', 'EnHGOTAq', 'ppLVDS', 'ppProbeOTAq',
               'ppLGOTAq', 'ppHGOTAq', 'EnBgap', 'ppBgap', 'EnDAC', 'ppDAC', 'DACslope', 'DAC', 'DiscriMask', 'LatchDiscri',
               'ppDiscri', 'EnDiscri', 'biasTandH', 'EnTandH', 'ppTandH', 'ppFS', 'EnFSh', 'ppFSFollow', 'TimeCHGSSh',
               'EnHGSSh', 'ppHGSSh', 'TimeCLGSSh', 'EnLGSSh', 'ppLGSSh', 'PreAmpCtest', 'LGPAComp', 'LGPAFback',
               'HGPAFback', 'HGPAComp', 'EnLGPA', 'ppLGPA', 'EnHGPA', 'ppHGPA', 'biasLGPA', 'Input8bitDAC', 'ref8bitDAC',
               'EnInputDAC'] 

class SetSlowControl:

    def __init__(self, sock, Dict):
        self.sock = SocketTCP.SocketTCP(sock)
        self.Dict = Dict
        pass

    def RunSCMode(self):
        Sig_SCMode = HeaderW + Addr_SCMode + SCMode
        Sig_SCMode = format(Sig_SCMode, '032b')

        self.sock.SendTCP(Sig_SCMode)
        Recv_Sig_SCMode = self.sock.RecvTCP(len(Sig_SCMode))

        if(Sig_SCMode and Recv_Sig_SCMode):
            #logger.debug('Set Slow Control Mode')
            print 'Set Slow Control Mode'
        else:
            logger.error('failure to send Slow Control Mode!!')
            return -1
            pass

        return 0
    
    def RunStartCycle(self):
        Sig_StartCycle = HeaderW + Addr_StartCycle + StartCycle
        Sig_StartCycle = format(Sig_StartCycle, '032b')
        
        self.sock.SendTCP(Sig_StartCycle)
        Recv_Sig_StartCycle = self.sock.RecvTCP(len(Sig_StartCycle))
        
        if(Sig_StartCycle and Recv_Sig_StartCycle):
            #logger.debug('Start Cycle is done......')
            print 'Start Cycle is done......'
        else:
            logger.error('failure to send Start Cycle!!')
            return -1
            pass

        return 0

    def RunLoadSC(self):
        Sig_LoadSC = HeaderW + Addr_LoadSC + LoadSC
        Sig_LoadSC = format(Sig_LoadSC, '032b')
        
        self.sock.SendTCP(Sig_LoadSC)
        Recv_Sig_LoadSC = self.sock.RecvTCP(len(Sig_LoadSC))
        
        if(Sig_LoadSC and Recv_Sig_LoadSC):
            #logger.debug('Load Slow Control data is done......')
            print 'Load Slow Control data is done......'
        else:
            logger.error('failure to send Load SC!!')
            return -1
            pass

        return 0
    
    def SetParameter(self, ChipAB):
        
        #which chip to be initialized(ChipA = 0, ChipB = 1)
        if(ChipAB):
            Chip = 'ChipB'
            Addr_Chip = (84 << 8)
        else:
            Chip = 'ChipA'
            Addr_Chip = (148 << 8)
            pass
        
        #send selected chip information to FPGA
        Chip_Mode = HeaderW + Addr_Chip
        Chip_Mode = format(Chip_Mode, '032b')
        
        self.sock.SendTCP(Chip_Mode)
        Recv_Chip_Mode = self.sock.RecvTCP(len(Chip_Mode))
        
        if(Chip_Mode and Recv_Chip_Mode):
            #logger.debug('Set Slow Control Parameters of %s:' %(Chip))
            print 'Set Slow Control Parameters of %s:' %(Chip)
        else:
            logger.error('failure to send chip select signal!!')
            return (-1, None)
        
        #initialize variable
        SumPar = ''

        #fill slow control parametes into variable
        for i in xrange(len(ParNameList)):
            
            #logger.debug('---> loading %s ......' %(ParNameList[i]))
            print '---> loading %s ......' %(ParNameList[i])
            
            NofBit = self.Dict['SlowCtrl_Setting'][Chip][ParNameList[i]]['NofBit']
            Par = self.Dict['SlowCtrl_Setting'][Chip][ParNameList[i]]['Value']
            
            for j in xrange(len(Par)):
                tmp = format(Par[j], '0%db' %(NofBit))
                SumPar += tmp
                logger.info('%s: %s[%02d] ---> %s(%d)' %(Chip, ParNameList[i], j, tmp, Par[j]))
                pass
            
            pass
        
        #reshape into array of 8bit data
        SlowCtrlData = [SumPar[i:i+8] for i in xrange(0, len(SumPar), 8)]
        
        if(len(SlowCtrlData) != 57 or len(SumPar) != 456):
            logger.error('Number of Slow Control Parameter is less or lager than 456 bit')
            logger.error('Please check the settings about Slow Control Paramters')
            return (-1, SumPar)

        #set Slow Control mode
        isSCMode = self.RunSCMode()

        if(isSCMode < 0):
            return (-1, SumPar)
        
        #send slow control data to FPGA
        for i in xrange(len(SlowCtrlData)):
            
            #initialize
            Data = 0
            
            #add header and address
            Data = HeaderW + Addr_Data + (int(SlowCtrlData[i], 2) << 8)
            Data = format(Data, '032b')
            
            #send data via TCP/IP
            self.sock.SendTCP(Data)
            Recv_Data = self.sock.RecvTCP(len(Data))
            
            #for debug
            Recv_Data = ((int(Recv_Data, 2) >> 8) & 255)
            Recv_Data = format(Recv_Data, '08b')
            
            logger.info('Send: %s ---> Recv: %s' %(SlowCtrlData[i], Recv_Data))
            
            pass

        #logger.debug('end of sending Slow Control Parameters of %s' %(Chip))
        print 'end of sending Slow Control Parameters of %s' %(Chip)
        
        #perform start cycle
        isStartCycle = self.RunStartCycle()

        if(isStartCycle < 0):
            return (-1, SumPar)
        
        isSCMode = self.RunSCMode()

        if(isSCMode < 0):
            return (-1, SumPar)
        
        #perforom load slow control data
        isLoadSC = self.RunLoadSC()

        if(isLoadSC < 0):
            return (-1, SumPar)
        
        isSCMode = self.RunSCMode()
        
        if(isSCMode < 0):
            return (-1, SumPar)

        return (0, SumPar)
    
