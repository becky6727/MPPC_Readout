import socket
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler

#----------------------------------------------------#
# class for socket connection for TCP/IP
# safer transfer/recieve data from readout module
# ver1.0: 2019/07/11 Y.Kibe
#----------------------------------------------------#

logger = getLogger('DAQ log').getChild('SocketTCP')
#logger.setLevel(logging.DEBUG)

class SocketTCP:

    #initialize
    def __init__(self, sock = None):
        if(sock == None):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
            pass
    
    #connect module at host(IP) and port
    def ConnectTCP(self, IP, port):
        try:
            self.sock.connect((IP, socket.htons(port)))
            #print 'Success to connect with TCP/IP'
            logger.warning('Success to connect with TCP/IP')
            return 0
        except socket.error as e:
            #print '***** !CONNENCTION ERROR! *****'
            #print e
            logger.error('***** !CONNENCTION ERROR! *****')
            logger.error(e)
            #print type(e)
            return -1
            pass
        
    def SendTCP(self, Data):
        TotalSent = 0
        LengthData = len(Data)
        while(TotalSent < LengthData):
            SentLength = self.sock.send(Data[TotalSent:])
            if(SentLength == 0):
                raise RuntimeError('socket conncetion(send) is broken!')
            TotalSent = TotalSent + SentLength
            
    #MSGLEN is length of sent Data by SendTCP
    def RecvTCP(self, MSGLEN = None):
        if(MSGLEN == None):
            raise RuntimeError('Length for receiving data is not set')
        chunks = []
        bytes_recd = 0
        while(bytes_recd < MSGLEN):
            chunk = self.sock.recv(min(MSGLEN - bytes_recd, 2048))
            if(chunk == b''):
                raise RuntimeError('socket connection(recv) broken')
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

        
    #close connection
    def CloseTCP(self):
        self.sock.close()
    
#end of definition
