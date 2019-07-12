import os, sys, time
import json
import socket
import argparse
import src.SocketTCP as SocketTCP
import struct

#---settings for EASIROC module at NPTC--------
# IPAddr = '192.168.10.11'
# PortID = 24
#---end of settings----------------------------

#---options---
parser = argparse.ArgumentParser(description = 'options for DAQ client')

parser.add_argument('-ip',
                    type = str,
                    dest = 'IPAddr',
                    default = '127.0.0.1',
                    help = 'set IP address of readout module, default is localhost')

parser.add_argument('-port',
                    type = int,
                    dest = 'PortID',
                    default = '50007',
                    help = 'set Port ID for TCP/IP connection to readout module')

args = parser.parse_args()

IPAddr = args.IPAddr
PortID = args.PortID

#time interval for timeout
Sec = 3
uSec = 0
Timeval = struct.pack('ll', Sec, uSec)

#socket for TCP/IP and optional settings
SockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SockTCP.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, Timeval)

#class for safer transfer/recieving
DAQSockTCP = SocketTCP.SocketTCP(SockTCP)

#connection
DAQSockTCP.ConnectTCP(IPAddr, PortID)

#dummy data
Data = 1 << 16
Data += 240 << 8
#Data += 3 << 8
Data = format(Data, '032b')

DAQSockTCP.SendTCP(Data)

Recv = DAQSockTCP.RecvTCP(len(Data))
#Recv = DAQSockTCP.RecvTCP()

print repr('Recieved Data = '+Recv), int(Recv, 2)

#confirm connection
#time.sleep(30)

#close
DAQSockTCP.CloseTCP()
