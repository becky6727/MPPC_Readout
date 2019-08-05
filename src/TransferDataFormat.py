import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler
import struct

#----------------------------------------------------#
# class for data format for TCP/IP
# ver1.0: 2019/08/02 Y.Kibe
#----------------------------------------------------#

logger = getLogger('DAQ log').getChild('TransferDataFormat')
#logger.setLevel(logging.DEBUG)

class TransferDataFormat:

    def __init__(self):
        pass

    #use for data transfer(read/write)
    def PackTCP(self, header, addr, data):

        #error check
        if(header < 0 or header > 0xff):
            logger.error('value of header is wrong!!')
            return -1

        if(addr < 0 or addr > 0xff):
            logger.error('value of address is wrong!!')
            return -1

        if(data < 0 or data > 0xff):
            logger.error('value of data is wrong!!')
            return -1

        #bit shift operation according to data format
        header = (header << 24)
        addr = (addr << 16)
        data = (data << 8)
        dummy = 0x0

        #pack into 4 byte data
        DataPack = struct.pack('!I', (header + addr + data + dummy))

        return DataPack
    
