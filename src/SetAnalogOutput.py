import src.SocketTCP as SocketTCP
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler

#-------------------------------------------------
# class for initializing Analog output settings
# ver1.0 2019/07/22 Y.Kibe
#-------------------------------------------------

logger = getLogger('DAQ log').getChild('SetAnalogOutput')
#logger.setLevel(logging.DEBUG)

#header for writing data
HeaderW = (128 << 24)

#address for analog output channel setting
Addr_Analog = (12 << 16)
Addr_SCMode = (1 << 16)
Addr_StartCycle = Addr_SCMode

#register for various modes
SCMode = (240 << 8)
StartCycle = (242 << 8)

class SetAnalogOutput:

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

    def SetParameter(self, ChipAB):

        #which chip to be initialized(ChipA = 0, ChipB = 1)
        if(ChipAB):
            Chip = 'ChipB'
            #Addr_Chip = (84 << 8)
        else:
            Chip = 'ChipA'
            #Addr_Chip = (148 << 8)
            pass

        #initialize variable
        SumPar = ''

        #fill analog output channel into variable
        NofBit = self.Dict['Analog_Output_Setting'][Chip]['ChSelect']['NofBit']
        Par = self.Dict['Analog_Output_Setting'][Chip]['ChSelect']['Value']

        for i in xrange(len(Par)):
            tmp = format(Par[i], '0%db' %(NofBit))
            SumPar += tmp
            logger.info('%s: Analog Output channel[%02d] ---> %s(%d)' %(Chip, i, tmp, Par[i]))
            pass

        #check number of channel to be selected(shold be 1)
        if(SumPar.count('1') > 1):
            logger.error('%s: number of channel for analog output shold be 1' %(Chip))
            logger.error('please confirm the configuration file')
            return (-1, SumPar)

        #reshape data
        AnalogChData = [SumPar[i:i+8] for i in xrange(0, len(SumPar), 8)]

        #send data
        for i in xrange(len(AnalogChData)):

            #initialize
            Data = 0

            #add header and address
            Data = HeaderW + Addr_Analog + (int(AnalogChData[i], 2) << 8)
            Data = format(Data, '032b')

            #send data via TCP/IP
            self.sock.SendTCP(Data)
            Recv_Data = self.sock.RecvTCP(len(Data))

            #for debug
            Recv_Data = ((int(Recv_Data, 2) >> 8) & 255)
            Recv_Data = format(Recv_Data, '08b')

            logger.info('Send: %s ---> Recv: %s' %(AnalogChData[i], Recv_Data))

            pass

        print 'end of sending Analog Output Channel setting of %s' %(Chip)

        #perform start cycle
        isStartCycle = self.RunStartCycle()

        if(isStartCycle < 0):
            return (-1, SumPar)

        isSCMode = self.RunSCMode()

        if(isSCMode < 0):
            return (-1, SumPar)

        return (0, SumPar)

    
