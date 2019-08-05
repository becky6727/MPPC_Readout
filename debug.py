import os, sys, time

EASIROC = raw_input('Copy and Paste of EASIROC Sample = \n')
MyCode = raw_input('Copy and Paste of my code = \n')

#replace
EASIROC = EASIROC.replace('.', '0').replace('!', '1')
MyCode = MyCode.replace('.', '0').replace('!', '1')

#slice
ArraySample = [EASIROC[i:i+8] for i in xrange(0, len(EASIROC), 8)]
ArrayMyCode = [MyCode[i:i+8] for i in xrange(0, len(MyCode), 8)]

if(len(ArrayMyCode) != len(ArraySample)):
    print 'not match length!'
    sys.exit()
    pass

print 'SampleCode <---> MyCode:'

for i in xrange(len(ArraySample)):

    isSame = False

    if(ArraySample[i] == ArrayMyCode[i]):
        isSame = True
        pass
    
    print '%s' %(ArraySample[i]),
    print '<---> %s' %(ArrayMyCode[i]),
    print '%s' %(isSame)
    
    pass

