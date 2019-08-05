import os, sys, time
import socket
import select
import Queue
import sitcpy
from sitcpy import to_bytearray
import struct
import random
#--------------------------------
# create dummy server for debug
# do not use except debugging
#--------------------------------

#AF_INET = IPv4
#SOCK_STREAM = TCP/IP
#SOCK_DGRAM = UDP

#IP and Port of server
IPAddr = '127.0.0.1'
PortID = 50007

#buffer
Buf = 8

#server for TCP/IP
ServerTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
#set IP address and port ID
ServerTCP.setblocking(0)
ServerTCP.bind((IPAddr, socket.htons(PortID)))

#server for UDP
ServerUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
#set IP address and port ID
ServerUDP.setblocking(0)
ServerUDP.bind((IPAddr, PortID))

#wait connection from client
#number of connection = 1
print 'wait for connection.....'
ServerTCP.listen(1)

inputs = [ServerTCP, ServerUDP]
outputs = []
DataQueue = {}
DataQueue[ServerUDP] = Queue.Queue()
AddrQueue = {}
AddrQueue[ServerUDP] = Queue.Queue()

Timeout = 30.0 #sec
isTimeout = False
isFinish = False
NofUDP = 0
LimitUDP = 0

def TransferRecvPacketTCP(header, addr, data):
    header = (header << 24)
    addr = (addr << 16)
    data = (data << 8)
    dummy = 0x0
    ret = struct.pack('!I', header + addr + data + dummy)
    return ret

def TransferRecvPacketUDP(ID, length, addr, data):
    ver_type = 0xff
    cmd_flag = 0xc8
    ret = struct.pack("8B",
                      ver_type,
                      cmd_flag,
                      ID,
                      length,
                      ((addr & 0xff000000) >> 24) & 0xff,
                      ((addr & 0x00ff0000) >> 16) & 0xff,
                      ((addr & 0x0000ff00) >> 8) & 0xff,
                      ((addr & 0x000000ff) >> 0) & 0xff)
    ret = ret + struct.pack('!B', int(data))
    return ret

def dummyDataGenerator():
    Chip = 0x81
    Ch = random.randrange(0, 32)
    tmpADC = int(random.gauss(2048, 512))
    ADC = (tmpADC & 0x0fff)
    var = struct.pack('!L', ((Chip << 24) + (Ch << 16) + ADC))
    return var

def dummyPacket(NofData, dummy):
    header1 = 0xffffea0c
    header2 = (NofData & 0xffff)
    header3 = 0x00000000
    tmp = struct.pack('!3L', header1, header2, header3)
    ret = tmp + dummy
    return ret

while inputs:

    (Rable, Wable, Except) = select.select(inputs, outputs, inputs, Timeout)

    if(Rable == [] and Wable == [] and Except == []):
        isTimeout = True
        pass
    
    for s in Rable:
        if(s is ServerTCP):
            #get socket and address of client
            (SockClientTCP, Addr) = s.accept()
            SockClientTCP.setblocking(0)
            inputs.append(SockClientTCP)
            DataQueue[SockClientTCP] = Queue.Queue()
            AddrQueue[SockClientTCP] = Queue.Queue()
        else:
            Data = s.recv(4096)    
            if(Data):
                
                if(s.type == 1):
                    Data = struct.unpack('!4B', Data)
                elif(s.type == 2):
                    Data = struct.unpack('!BBBBIB', Data)
                    pass
                
                #display data from client
                #print 'data: {}, address: {}'.format(format(int(Data[0]), '032b'), Addr)
                if(s.type == 1):
                    print 'recv from user = %s, %s, %s' %(format(Data[0], '02x'),
                                                          format(Data[1], '02x'),
                                                          format(Data[2], '02x'))
                elif(s.type == 2):
                    print 'ver-type = %s' %(format(Data[0], '02x'))
                    print 'cmd-flag = %s' %(format(Data[1], '02x')) 
                    print 'ID = %s' %(format(Data[2], '02x')) 
                    print 'length = %s' %(format(Data[3], '02x')) 
                    print 'address = %s' %(format(Data[4], '04x')) 
                    print 'data = %s' %(format(Data[5], '02x')) 
                    pass
                DataQueue[s].put(Data)
                AddrQueue[s].put(Addr)
                if(s not in outputs):
                    outputs.append(s)
                    pass
            else:
                if(s in outputs):
                    outputs.remove(s)
                    pass
                inputs.remove(s)
                s.close()
                del DataQueue[s]
                pass
            pass
        pass
    
    for s in Wable:
        try:
            NextData = DataQueue[s].get_nowait()
            NextAddr = AddrQueue[s].get_nowait()
        except Queue.Empty:
            outputs.remove(s)
        else:
            if(s.type == 1):
                AckData = TransferRecvPacketTCP(NextData[0], NextData[1], NextData[2])
                s.send(AckData)    
                if(NextData[0] == 0x80 and NextData[1] == 0x64):
                    for i in xrange(0, 10000):
                        ndata = random.randrange(1, 11)
                        tmpAck = ''
                        for j in xrange(0, ndata):
                            tmp = dummyDataGenerator()
                            tmpAck += tmp
                            pass
                        AckData = dummyPacket(ndata, tmpAck)
                        s.send(AckData)
                        pass
                    pass
            elif(s.type == 2):
                #time.sleep(0.01)
                AckData = TransferRecvPacketUDP(NextData[2], NextData[3], NextData[4], NextData[5])
                s.sendto(AckData, NextAddr)
                pass
            pass
        pass

    for s in Except:
        inputs.remove(s)
        if(s in outputs):
            outputs.remove(s)
            pass
        s.close()
        del DataQueue[s]
        pass
    
    if(isTimeout):
        print 'Timeout signal is detected!'
        break
    
    pass

ServerTCP.close()
ServerUDP.close()
