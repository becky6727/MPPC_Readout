import os, sys, time, datetime
import json
import socket
import argparse
import src.SocketTCP as SocketTCP
import struct
import logging
from logging import getLogger, StreamHandler, Formatter, FileHandler
import src.SetFPGA as SetFPGA
import src.SetSlowControl as SetSlowControl
import src.SetAnalogOutput as SetAnalogOutput
import src.SetDAQ as SetDAQ
import src.SetUDPCtrl as SetUDPCtrl
#from sitcpy import to_bytes, to_bytearray
import numpy

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

parser.add_argument('-config',
                    type = str,
                    dest = 'FileConfig',
                    default = './config/Settings.json',
                    help = 'set configuration file')

parser.add_argument('-daq',
                    type = int,
                    dest = 'DAQMode',
                    default = '3',
                    help = 'set DAQ mode(ADC, TDC, or ADC & TDC)')

args = parser.parse_args()

#log file settings
dt_now = datetime.datetime.now()
Log = './log/%04d-%02d-%02d_%02dh%02dm%02ds.log' %(dt_now.year, dt_now.month, dt_now.day,
                                                   dt_now.hour, dt_now.minute, dt_now.second)
logger = getLogger('DAQ log')
logger.setLevel(logging.DEBUG)

handler_format = Formatter('%(asctime)s: %(name)s, %(levelname)s, %(message)s')

stream_handler = StreamHandler()
#stream_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.WARNING)
#stream_handler.setLevel(logging.ERROR) #if want to show no info
stream_handler.setFormatter(Formatter('%(message)s'))

file_handler = FileHandler(Log, 'a')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(handler_format)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

#IP address and port ID for TCP/IP
IPAddr = args.IPAddr
PortID = args.PortID

#time interval for timeout
Sec = 3
uSec = 0
Timeval = struct.pack('ll', Sec, uSec)

#socket for TCP/IP and optional settings
SockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SockTCP.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, Timeval)
SockTCP.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

#class for safer transfer/recieving
DAQSockTCP = SocketTCP.SocketTCP(SockTCP)

#connection
isConnectTCP = DAQSockTCP.ConnectTCP(IPAddr, PortID)

#if connection error occur...
if(isConnectTCP < 0):
    sys.exit()
    pass

#load configuration file
FileConfig = args.FileConfig
ConfigDict = json.load(open(FileConfig, 'r'))

