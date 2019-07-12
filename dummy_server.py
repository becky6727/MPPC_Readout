import os, sys, time
import socket

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

Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
#set IP address and port ID
Server.bind((IPAddr, PortID))
    
#wait connection from client
#number of connection = 1
print 'wait for connection.....'
Server.listen(1)

#get socket and address of client
(SockClient, Addr) = Server.accept()

SockClient.settimeout(1)

#main loop
while True:

    #recieve data from client with buffer
    Data = SockClient.recv(Buf)
    
    if(not(Data)):
        break
    
    #display data from client
    print 'data: {}, address: {}'.format(Data, Addr)
    
    #return data to client
    SockClient.send(b''+Data)
    
    pass

SockClient.close()
Server.close()
