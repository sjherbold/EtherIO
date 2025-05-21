#!/usr/bin/python3
import sys
from time import sleep, time
from eio import *

def test(dev=None, delay=0.25, max=None):
    """ Simple walking ones test across port """
    if not dev:       dev = eio24r(eaddr)
    if isdevice(dev): port = dev.porta
    if isport(dev):   port = dev
    print('test:',port)
    port.dir = PORTDIROUTPUT
    lites = [1,2,4,8,16,32,64,128,0]
    cnt = 0
    while True:
        for led in lites:
            port.val = led
            sleep(delay)
        cnt += 1
        if cnt == max : break

def cylon(dev=None, delay=0.05, max=None):
    """ Cylon Eye """
    if not dev: dev = eio24r(eaddr)
    print('Cylon:',dev)
    dev.porta.dir = PORTDIROUTPUT
    lites = [1,2,4,8,16,32,64,128,64,32,16,8,8,2]
    cnt = 0
    while True:
        for led in lites:
            dev.porta.val = led
            sleep(delay)
            cnt += 1
            if cnt == max : return

def ioout(dev=None, delay=0.05, max=None):
    """ Example of using io numbers """
    if not dev: dev = eio24r(eaddr)
    print('Pin IO:',dev)
    dev.porta.dir = PORTDIROUTPUT
    cnt = 0
    while True:
        for v in (1,0):
            for p in range(0,8):
                dev.io[p] = v
                sleep(delay)
        cnt += 1
        if cnt == max : return

def count(dev=None, delay=0.05, max=None):
    """ Count up """
    if not dev: dev = eio24r(eaddr)
    print('Counting up:',dev)
    dev.porta.dir = PORTDIROUTPUT
    cnt = 0
    while True:
        for led in range(0,256):
            dev.porta.val = led
            sleep(delay)
            cnt += 1
            if cnt == max : return

def divide(dev=None, delay=0.1, max=None):
    """ Divide """
    if not dev: dev = eio24r(eaddr)
    print('Divide:',dev)
    dev.porta.dir = PORTDIROUTPUT
    lites = [0x18,0x24,0x42,0x81,0x00]
    cnt = 0
    while True:
        for led in lites:
            dev.porta.val = led
            sleep(delay)
            cnt += 1
            if cnt == max : return

def wiggle(dev=None, delay=0.1, max=None):
    """ Wiggle """
    if not dev: dev = eio24r(eaddr)
    print('Wiggle:',dev)
    dev.porta.dir = PORTDIROUTPUT
    lites = [0x55,0xAA,0x55,0xAA]
    cnt = 0
    while True:
        for led in lites:
            dev.porta.val = led
            sleep(delay)
            cnt += 1
            if cnt == max : return

def loopbacktest(dev=None, delay=0.010, wait=0.010, reportevery=1000, max=None):
    """
    run test on an eio24 module with loopback cable between port b & c
    
    porta : output random value for monitor using LED board
    portb : output same value number on port and loop back
    portc : input loop back data
    
    A random value is generated and written to porta and portb. The output of portb is
    read back on portc using a loopback cable. The values are tested to make sure they
    match. If they do not match, they are read and checked again. If this does not
    match the test will exit.
    
    delay       : delay time in seconds between each loop iteration
    wait        : wait time in seconds before reading back ports
    reportevery : print out a progress report every n'th time (None or zero is never)
    max         : maximum number of loop iterations (None or zero is forever)
    """
    import random
    
    if not dev: dev = eio24r(eaddr)
    print('Loopback test:',dev)
    dev.porta.dir = PORTDIROUTPUT
    dev.portb.dir = PORTDIROUTPUT
    dev.portc.dir = PORTDIRINPUT
    
    loopcnt = 0
    last = -1
    tstart = time()
    tlast  = tstart
    while True:
        num = random.randint(0,255)
        dev.porta.val = num
        dev.portb.val = num
        sleep(wait)
        a = dev.porta.val
        b = dev.portb.val
        c = dev.portc.val
        if not (a == b == c) :
            print('num={:3d} a={:3d} b={:3d} c={:3d} last={:3d}'.format(num,a,b,c,last))
            #try again?
            a = dev.porta.val
            b = dev.portb.val
            c = dev.portc.val
            if not (a == b == c) :
                break
        loopcnt += 1
        if reportevery and (loopcnt % reportevery) == 0 :
            tnow   = time()
            tdiff  = tnow - tlast
            ttotal = tnow - tstart
            print('loopcnt={} tdiff={:.3f} ttotal={:.3f}'.format(loopcnt,tdiff,ttotal))
            print(eioudp.stats())
            tlast = tnow
        if loopcnt == max : break
        last = num
        sleep(delay)


if __name__ == "__main__":
    if len(sys.argv)==2:
        eaddr = sys.argv[1] 
    else:
        a = input('Enter your EtherIO device ip adddress ({}):'.format(eaddr))
        if a : eaddr = a
    test(max=10)
    cylon(max=100)
    divide(max=10)
    wiggle(max=100)
    ioout(max=10)
    count(max=257)

