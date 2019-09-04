import os, sys, time
import numpy
import struct

binary_data = open('./Data/Run0091.dat', 'rb').read()

print len(binary_data)

isHeader = [False, False, False]

for i in xrange(0, len(binary_data), 4):

    try:
        data = struct.unpack_from('4B', binary_data, i)
    except struct.error:
        break
    else:
        #print (format(data[3], '02x'), format(data[2], '02x'),
        #       format(data[1], '02x'), format(data[0], '02x'))
        header = data[0] + (data[1] << 8)
        pass

    if(header == 0xea0c):
        isHeader[0] = True
        isHeader[2] = False
        continue
    
    if(isHeader[0]):
        NofData = (data[1] << 8) + data[0]
        isHeader[0] = False
        isHeader[1] = True
        continue

    #print NofData
    
    if(isHeader[1]):
        EvtCnt = (data[3] << 8) + data[2]
        isHeader[2] = True
        isHeader[1] = False
        continue

    if(isHeader[2]):
        ChipID = data[3] & 0xff
        ChNo = data[2] & 0x1f
        ADC = ((data[1] & 0x0f) << 8) + data[0]
        OverFlow = (data[1] & 0x10)
        if(ChipID != 0x81):
            Chip = 'B'
        else:
            Chip = 'A'
            pass
        #print 'id: %s, ch: %d' %(format(ChipID, '02x'), ChNo)
        print 'id: %s, ch: %d, ADC: %d' %(Chip, ChNo, ADC)
        pass
    
    pass

