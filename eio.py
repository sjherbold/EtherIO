#!/usr/bin/python3
#
# Copyright 2025 Steven Herbold
# SPDX-License-Identifier: MIT
# keywords: Elexol, EtherIO, Ether IO24 R, Ether IO24 TCP, Ether IO72 TCP, EtherIO24, EtherIO72, IO24R, IO24T, IO72T
#
from time import sleep, time
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM    

# configuration
eaddr = '10.10.10.10:2424'    # elexol device IP:Port, this is one of the defaults through jumper setting
PORTDIRINPUT  = 0xFF
PORTDIROUTPUT = 0x00

class eiobase:
    """
    Shared base class of all eio objects for common functions
    """
    
    def __init__(self, kind, ipaddr, ipport=None):
        """
        kind is one of ['IO24R','IO24T','IO72T']
        ipaddr is the ip address of the module
        ipport is the port address of the module if not the default or included in the ipaddr
        """
        
        kinds = ['IO24R','IO24T','IO72T']
        if kind not in kinds : raise ValueError(f'Device kind must be one of {kinds}')
        
        #address stored as a tuple of (address,port)
        self.ipaddr = addrtuple(ipaddr)
        if ipport : self.ipaddr = (self.ipaddr[0], ipport)   #override ipport passed in from the address or the default
        self.kind   = kind
        
        if kind in ['IO24R','IO24T','IO72T'] :
            self.porta = self.__port("A",self)
            self.portb = self.__port("B",self)
            self.portc = self.__port("C",self)
            self.ports = [self.porta, self.portb, self.portc]
        if kind in ["IO72T"] :
            self.portd = self.__port("D",self)
            self.porte = self.__port("E",self)
            self.portf = self.__port("F",self)
            self.portg = self.__port("G",self)
            self.porth = self.__port("H",self)
            self.porti = self.__port("I",self)
            self.ports += [ self.portd, self.porte, self.portf, self.portg, self.porth, self.porti ]
        
        self.io = self.__io(self)
        
    class __port:
        """ port control using dot notation, portx.[val|dir|pup|thr|sch] """
        
        def __init__(self, port, eio):
            self.eio  = eio    #outer class reference for attributes ipaddr & ipport
            self.port = port   #port letter

        def __str__(self):
            return f'port{self.port.lower()} of {self.eio.__str__()}'
        
        #create low level eio command to get port register data
        def _pget(self, s):
            if s and (s in "#$") and (self.eio.kind != "IO24R") : 
                # only IO24R has sch and thr attributes
                raise AttributeError(f'{self.eio.kind} does not have this attribute')
            c = bytes(s,'utf-8') + self.port.lower().encode()
            d = eioudp.cmd(c, self.eio.ipaddr)
            return d[-1]   #the data is the last byte of the returned command response
        
        #create low level eio command to set port register data
        def _pset(self, s, v):
            if s and (s in "#$") and (self.eio.kind != "IO24R") : 
                # only IO24R has sch and thr attributes
                raise AttributeError(f'{self.eio.kind} does not have this attribute')
            c = bytes(s,'utf-8') + self.port.upper().encode() + bytes((v,))
            eioudp.cmd(c, self.eio.ipaddr)
        
        # these are class properties/attributes for the port
        val = property(lambda self: self._pget(''),  lambda self,v: self._pset('',v),  doc="port value")
        dir = property(lambda self: self._pget('!'), lambda self,v: self._pset('!',v), doc="port direction")
        pup = property(lambda self: self._pget('@'), lambda self,v: self._pset('@',v), doc="port pullup")
        thr = property(lambda self: self._pget('#'), lambda self,v: self._pset('#',v), doc="port threshold")
        sch = property(lambda self: self._pget('$'), lambda self,v: self._pset('$',v), doc="port schmitt")
        # Note: IO24T/IO72T
        # Legacy Pullup Command '@' is still implemented for backward compatibility, 
        # however it is advised to use the new '%' command on any new development.
    
    
    class __io:
        """ 
        pin io manipulation using dev.io[p] format 
        
        Where p is the pin io number from 0 to n (n=23 on IO24, n=71 on IO72)
        
        Returns either 0 or 1
        
        Can be set to:
            0 with any value in the list of [0,'0','L','LO','LOW', 'OFF']
            1 with any value in the list of [1,'1','H','HI','HIGH','ON' ]
        """
        
        def __init__(self, eio):
            self.eio  = eio    #outer class reference
            if (self.eio.kind in ["IO24R","IO24T"]) : self.len = 24 
            if (self.eio.kind in ["IO72T"])         : self.len = 72
        
        def __len__(self):
            return self.len
        
        def _iochk(self, io):
            """verify io in range and return tuple of (port,bit,bitmask)"""
            if not isinstance(io, int):
                raise TypeError("Index must be an integer")
            if  (io<0 or io>=self.len) : 
                raise IndexError(f'Index out of range: {self.eio.kind} io range from 0 - {self.len-1} inclusive')
            prt,bit = divmod(io,8)
            msk = 1<<bit
            return (prt,bit,msk)
            
        def __getitem__(self, io):
            prt,bit,msk = self._iochk(io)
            val = self.eio.ports[prt].val
            #print(f'{prt=} {bit=} {msk=} {val=}')
            return( 1 if (val & msk) else 0 ) 
        
        def __setitem__(self, io, v):
            LOs = [0,'0','L','LO','LOW', 'OFF']
            HIs = [1,'1','H','HI','HIGH','ON' ]
            if v not in LOs + HIs:
                raise ValueError(f'{self.eio.kind} io values in {LOs+HIs}')
            prt,bit,msk = self._iochk(io)
            val = self.eio.ports[prt].val
            if v in LOs: val = val & (msk ^ 0xFF)
            if v in HIs: val = val | msk
            self.eio.ports[prt].val = val
        
        def __delitem__(self, io):
            pass
    
    def _get_ee_ip(self, reg):
        w1 = eeprom_readword(self.ipaddr, reg+0)
        w2 = eeprom_readword(self.ipaddr, reg+1)
        return f'{w1[1]}.{w1[0]}.{w2[1]}.{w2[0]}'
    
    def _set_ee_ip(self, reg, val):
        val = [ int(x) for x in val.split('.') ]
        eeprom_writeword(self.ipaddr, reg+0, bytes((val[1],val[0])))
        eeprom_writeword(self.ipaddr, reg+1, bytes((val[3],val[2])))
        return None
    
    _doc_ee_ip = """gets or sets the value stored in the eeprom using a dot separated string"""
    
    # eeprom properties
    eeprom_ipaddr = property(lambda self: self._get_ee_ip(6),  lambda self,v: self._set_ee_ip(6,v),  doc=_doc_ee_ip + ", i.e. '192.168.1.10'")
    eeprom_ipmask = property(lambda self: self._get_ee_ip(25), lambda self,v: self._set_ee_ip(25,v), doc=_doc_ee_ip + ", i.e. '255.255.255.0'")
    eeprom_ipgway = property(lambda self: self._get_ee_ip(27), lambda self,v: self._set_ee_ip(27,v), doc=_doc_ee_ip + ", i.e. '192.168.1.1'")
    

def isdevice(obj):
    return isinstance(obj,eiobase)

def isport(obj):
    return isinstance(obj,eiobase._eiobase__port)


class eio24t(eiobase):
    """    
    Create an eio object that can reference the device through dot notation using
    the port and register names, for example:
    
       dev = eio24t('192.168.1.123') #create object at ipaddr using default ipport
       x = dev.porta.val             #return the current setting of value at port a
       dev.porta.val = 123           #set port a to 123
    
    Port names:  porta, portb, portc
    
    Register names: 
        val     port input or output value
        dir     port direction (0=output, 1=input)
        pup     port pullup resistor (0=enabled, 1=disabled)
    
    Each register is composed of 8 bits which correspond to the 8 I/O lines
    
    Each pin can be individually manipulated using indexing into the dev.io[] object.
    """
    
    def __init__(self, ipaddr, ipport=None):
        super().__init__("IO24T", ipaddr, ipport)
    
    def __str__(self):
        return f"eio24t device at {self.ipaddr}"
    
    def reset(self):
        """Send reset command to the device ('@)"""
        eioudp.cmd(b"'@", self.ipaddr)
        sleep(0.010)  #allow device to perform reset operations
    
    @property
    def mac(self):
        """Retrieve the mac address from the device"""
        return (eioudp.mac(b"IO24", self.ipaddr))

class eio72t(eiobase):
    """    
    Create an eio object that can reference the device through dot notation using
    the port and register names, for example:
    
       dev = eio72t('192.168.1.123') #create object at ipaddr using default ipport
       x = dev.porta.val             #return the current setting of value at port a
       dev.porta.val = 123           #set port a to 123
    
    Port names:  porta, portb, portc, portd, porte, portf, portg, porth, porti
    
    Register names: 
        val     port input or output value
        dir     port direction (0=output, 1=input)
        pup     port pullup resistor (0=enabled, 1=disabled)
    
    Each register is composed of 8 bits which correspond to the 8 I/O lines
    
    Each pin can be individually manipulated using indexing into the dev.io[] object.
    """
    
    def __init__(self, ipaddr, ipport=None):
        super().__init__("IO72T", ipaddr, ipport)    
    
    def __str__(self):
        return f"eio72t device at {self.ipaddr}"
    
    def reset(self):
        """Send reset command to the device ('@)"""
        eioudp.cmd(b"'@", self.ipaddr)
        sleep(0.010)  #allow device to perform reset operations
    
    @property
    def mac(self):
        """Retrieve the mac address from the device"""
        return (eioudp.mac(b"'IO72", self.ipaddr))
    

class eio24r(eiobase):
    """    
    Create an eio object that can reference the device through dot notation using
    the port and register names, for example:
    
       dev = eio24r('192.168.1.123') #create object at ipaddr using default ipport
       x = dev.porta.val             #return the current setting of value at port a
       dev.porta.val = 123           #set port a to 123
    
    Port names:  porta, portb, portc
    
    Register names: 
        val     port input or output value
        dir     port direction (0=output, 1=input)
        pup     port pullup resistor (0=enabled, 1=disabled)
        thr     port threshold (0=2.5V, 1=1.4V)
        sch     port schmitt enable (0=enbled, 1=disabled)
    
    Each register is composed of 8 bits which correspond to the 8 I/O lines
    
    Each pin can be individually manipulated using indexing into the dev.io[] object.
    """
    
    def __init__(self, ipaddr, ipport=None):
        super().__init__("IO24R", ipaddr, ipport)
   
    def __str__(self):
        return f"eio24r device at {self.ipaddr}"
    
    def reset(self):
        """Send reset command to the device ('@\\x00\\xAA\\x55)"""
        eioudp.cmd(b"'@\x00\xAA\x55", self.ipaddr)
        sleep(0.010)  #allow device to perform reset operations
    
    @property
    def mac(self):
        """Retrieve the mac address from the device"""
        return (eioudp.mac(b"IO24", self.ipaddr, retries=None))
    
    def eeprom_enable(self):
        '''enable write access to the eeprom memory'''
        eioudp.cmd(b"'1\x00\xAA\x55", self.ipaddr)
    
    def eeprom_disable(self):
        '''disable write access to the eeprom memory'''
        eioudp.cmd(b"'0\x00\xAA\x55", self.ipaddr)

class eioudp:
    """ etherio udp command driver """
    
    #global control
    timeout = 1
    retries = 10
    write_validate = True
    retry_delay = 0.010
    
    def settings():
        """
        Returns a dictionary of command interface settings
        
            timeout        : read timeout for udp
            retries        : number of times to retry a failed read or write command
            write_validate : True/False to perform write validation
            retry_delay    : delay between subsequent retry attempts
        """
        s = {'timeout':eioudp.timeout, 'retries':eioudp.retries, 'write_validate':eioudp.write_validate, 'retry_delay':eioudp.retry_delay}
        return(s)
    
    #function statistics
    _cnt_cmds = 0
    _cnt_pkts = 0
    _cnt_rd_retries = 0
    _cnt_wr_retries = 0
    _max_rd_retries = 0
    _max_wr_retries = 0
    
    def stats():
        """
        Returns a dictionary of statistics of the command interface
        
            ttl_cmds       : number of commands sent
            ttl_pkts       : number of udp packets sent
            ttl_rd_retries : number of times a read retry was initiated
            ttl_wr_retries : number of times a write retry was initiated
            max_rd_retry   : maximum attempts for any one read retry
            max_wr_retry   : maximum attempts for any one write retry
        """
        s = {'ttl_cmds':eioudp._cnt_cmds, 'ttl_pkts':eioudp._cnt_pkts, 'ttl_rd_retries':eioudp._cnt_rd_retries, 'ttl_wr_retries':eioudp._cnt_wr_retries, 'max_rd_retry':eioudp._max_rd_retries, 'max_wr_retry':eioudp._max_wr_retries}
        return(s)
    
    def stats_clear():
        """
        Clear statistics counters
        """
        eioudp._cnt_cmds = 0
        eioudp._cnt_pkts = 0
        eioudp._cnt_rd_retries = 0
        eioudp._cnt_wr_retries = 0
        eioudp._max_rd_retries = 0
        eioudp._max_wr_retries = 0
    
    _maxrecvfrom = 1024
    _last_exception = None
    
    def cmd(cmd, addr, retries=None):
        """
        Sends cmd bytes to an etherio device, returns data if any (or None).
        
        cmd  : byte(s)
        addr : tuple(str,int), i.e. ('192.168.1.123',2424) of address ip and port 

        does minor syntax checking of the cmd, raises ValueError if issue
        
        Reference the command Set Quick Reference in the datasheet for full
        command explanation, ascii, hex, byte count, ...
        
        Note: this is a very low level command interface and it is easier to 
        use the eio24 class interface with port and register names.
        
        Uses UDP packets, which may be unreliable, so includes read timeout retries
        and write verification readback with retry for some write commands.
        
        """
        
        if retries is None : retries = eioudp.retries #if not overridden, use the global setting
        
        cmdtype = _cmdcheck(cmd)
        if not cmdtype:
            raise ValueError("bad eio command:",cmd)
        
        #send out the command packet and receive the response if any
        eioudp._cnt_cmds += 1
        tries = 0
        while True:
            with socket(AF_INET, SOCK_DGRAM) as mySocket:
                mySocket.settimeout(eioudp.timeout)
                try:
                    mySocket.sendto(cmd, addr)
                    eioudp._cnt_pkts += 1
                    if cmdtype == 'read':
                        (data, _) = mySocket.recvfrom(eioudp._maxrecvfrom) 
                        eioudp._cnt_pkts += 1
                    else:
                        data = None
                except Exception as e:
                    # this is a little broad, but we will handle any socket error the same and eventually timeout on retrys
                    eioudp._last_exception = e
                    eioudp._cnt_rd_retries += 1
                    tries += 1
                    if tries > retries: raise TimeoutError
                    if tries > eioudp._max_rd_retries : eioudp._max_rd_retries = tries
                    sleep(eioudp.retry_delay)
                else:
                    break
        
        if eioudp.write_validate and cmdtype == 'verify' :
            msk = 0xFF
            if cmd[:1] in b'ABCDEFGHI':
                #write was to the output register which only works on bits set for output in the dir regisiter
                #read the dir register for this port and create a mask
                dir = eioudp.cmd(b'!'+cmd[:1].lower(), addr)[-1]
                msk = dir ^ 0xFF
            vcmd = cmd[:-1].lower()
            tries = 0
            while True:
                val = eioudp.cmd(vcmd,addr)                    #use our function to get read retries without adding same logic here
                eioudp._cnt_cmds -= 1                          #take our extra command off the count of official commands
                #print(f'{val.hex()=} {cmd.hex()=} {msk=:02x}')
                if (val[-1] & msk) == (cmd[-1] & msk) : break  #write was successful, break out of retry loop
                #resend original write command
                with socket(AF_INET, SOCK_DGRAM) as mySocket:
                    mySocket.settimeout(eioudp.timeout)
                    try:
                        mySocket.sendto(cmd, addr)
                        eioudp._cnt_pkts += 1
                    except Exception as e:
                        eioudp._last_exception = e
                eioudp._cnt_wr_retries += 1
                tries += 1
                if tries > retries: raise TimeoutError
                if tries > eioudp._max_wr_retries : eioudp._max_wr_retries = tries
                sleep(eioudp.retry_delay)
        return data
    
    def mac(cmd, addr, retries=None):
        try:
            rsp = eioudp.cmd(cmd, addr, retries)
            return rsp[4:10].hex().upper()
        except TimeoutError:
            return None
    
def eeprom_ipaddr(addr):
    """return the ip address programmed into the device eeprom (use the device eeprom_ipaddr attribute instead of this)"""
    if isinstance(addr,eiobase) : addr = addr.ipaddr
    w6 = eeprom_readword(addr, 6)
    w7 = eeprom_readword(addr, 7)
    return w6[1],w6[0],w7[1],w7[0]

def eeprom_ipmask(addr):
    """return the ip address mask programmed into the device eeprom (use the device eeprom_ipmask attribute instead of this)"""
    if isinstance(addr,eiobase) : addr = addr.ipaddr
    w25 = eeprom_readword(addr, 25)
    w26 = eeprom_readword(addr, 26)
    return w25[1],w25[0],w26[1],w26[0]

def eeprom_ipgway(addr):
    """return the ip address gateway programmed into the device eeprom (use the device eeprom_ipgway attribute instead of this)"""
    if isinstance(addr,eiobase) : addr = addr.ipaddr
    w27 = eeprom_readword(addr, 27)
    w28 = eeprom_readword(addr, 28)
    return w27[1],w27[0],w28[1],w28[0]

def eeprom_readword(addr, reg):
    if isinstance(addr,eiobase) : addr = addr.ipaddr
    rsp = eioudp.cmd(b"'R"+bytes((reg,))+b"\x00\x00", addr)
    return rsp[-2:]

def eeprom_writeword(addr, reg, val):
    if isinstance(addr,eiobase) : addr = addr.ipaddr
    eioudp.cmd(b"'W"+bytes((reg,))+val, addr)
    sleep(0.010) #allow time for the write to complete

def eeprom_image(addr):
    """returns an array of ints for the bytes in the eeprom"""
    if isinstance(addr,eiobase) : addr = addr.ipaddr
    image = []
    for reg in range(0,64):
        word = eeprom_readword(addr, reg)
        image.append(word[1])
        image.append(word[0])
    return image

def addrtuple(obj):
    """convert various address/port representations into common format"""
    
    addr,port = None,None
    
    if type(obj) is tuple and len(obj) == 2 : addr,port = obj                      # ('192.168.1.10',2424)
    if type(obj) is tuple and len(obj) == 4 : addr,port = obj, None                # ( 192,168,1,10 )
    if type(obj) is tuple and len(obj) == 5 : addr,port = obj[0:4], obj[4]         # ( 192,168,1,10,2424 )
    if type(obj) is str                     : addr,port,*_ = (obj+':').split(':')  # '192.168.1.10:2424','192.168.1.10' 
    
    if type(addr) is tuple: addr = '.'.join(map(str,addr))
    if not addr :           addr = '10.10.10.10'
    if not port :           port = 2424
    if type(port) is str:   port = int(port)
    
    return(addr,port)

def _cmdcheck(cmd):
    """return type of command read, write, write-verify, or None if bad"""
    #note: use slicing for bytes to return a byte, simple indexing returns an int from a byte object
    
    #identify command
    if cmd == b"IO24": return 'read'    #part identify with MAC and SW version (IO24)
    if cmd == b"'IO72": return 'read'   #part identify with MAC and SW version (IO72)
    
    #normalize command syntax, use _ to make val register command same as other register commands
    if not cmd or (cmd[:1] == b'_') : return None
    if cmd[:1] in b'abcdefghiABCDEFGHI' : cmd = b'_' + cmd

    #read register value,direction,pullup,threshold,schmitt
    if (len(cmd) == 2) and (cmd[0:1] in b'_!@#$%') and (cmd[1:2] in b'abcdefghi') : return 'read'

    #write register value,direction,pullup,threshold,schmitt
    if (len(cmd) == 3) and (cmd[0:1] in b'_!@#$%') and (cmd[1:2] in b'ABCDEFGHI') : return 'verify'
    
    #eeprom commands legacy and IO24R
    if (len(cmd) == 5) and (cmd[:2] == b"'R") :   return 'read'                      #eeprom read word
    if (len(cmd) == 5) and (cmd[:2] == b"'W") :   return 'write'                     #eeprom write word
    if (len(cmd) == 5) and (cmd[:2] in [b"'E",b"'0",b"'1"]) : return 'write'         #eeprom erase, write disable, write enable
    #eeprom commands IO24T/IO72T new commands
    if (len(cmd) == 4) and (cmd[:2] == b"'r") :   return 'read'                      #eeprom read byte
    if (len(cmd) == 5) and (cmd[:2] == b"'w") :   return 'write'                     #eeprom write byte
    
    ### the IO24T and IO72T module commands differ?  H vs 'H  ?
    # #io commands
    # if (len(cmd) == 3) and (cmd[:2] == b"'H") :   return 'write'  #raise IO pin
    # if (len(cmd) == 3) and (cmd[:2] == b"'L") :   return 'write'  #lower IO pin
    
    #reset command
    if cmd[:2] == b"'@" and len(cmd) == 5: return 'write'   #reset device IO24R
    if cmd[:2] == b"'@" and len(cmd) == 2: return 'write'   #reset device IO24T & IO72T
    
    #SPI commands
    if cmd == b'S1A':    return 'read'   #set up port for SPI, response should be b'S1A'
    if cmd == b'S0A':    return 'read'   #set up port for SPI, response should be b'S0A'
    if cmd[:2] == b'SA': return 'read'   #
    
    return None
    
class eiotcp:
    """ etherio tcp command driver - UNTESTED"""
    
    #global control
    timeout = 1
    retries = 10
    write_validate = True
    retry_delay = 0.010
    
    def settings():
        """
        Returns a dictionary of command interface settings
        
            retries        : number of times to retry a failed read or write command
            retry_delay    : delay between subsequent retry attempts
        """
        s = {'retries':eiotcp.retries, 'retry_delay':eiotcp.retry_delay}
        return(s)
    
    #function statistics
    _cnt_cmds = 0
    _cnt_retries = 0
    
    def stats():
        """
        Returns a dictionary of statistics of the command interface
        
            ttl_cmds       : number of commands sent
            ttl_retries    : number of times a read or write retry was initiated
        """
        s = {'ttl_cmds':eiotcp._cnt_cmds, 'max_retry':eiotcp._max_wr_retries}
        return(s)
    
    def stats_clear():
        """
        Clear statistics counters
        """
        eiotcp._cnt_cmds = 0
        eiotcp._max_retries = 0
    
    _maxrecvfrom = 1024
    
    
    def cmd(cmd, addr):
        """
        Sends cmd bytes to an etherio device, returns data if any (or None).
        
        cmd  : byte(s)
        addr : str, i.e. 192.168.1.123

        does minor syntax checking of the cmd, raises ValueError if issue
        
        Reference the command Set Quick Reference in the datasheet for full
        command explanation, ascii, hex, byte count, ...
        
        Note: this is a very low level command interface and it is easier to 
        use the eio24/eio72 class interface with port and register names.
        
        Uses TCP packets.
        
        """
        
        cmdtype = _cmdcheck(cmd)
        if not cmdtype:
            raise ValueError("bad eio command:",cmd)
        
        #send out the command packet and receive the response if any
        eiotcp._cnt_cmds += 1
        tries = 0
        while True:
            with socket(AF_INET, SOCK_STREAM) as mySocket:
                try:
                    mySocket.connect(addr)
                    mySocket.sendall(cmd)
                    if cmdtype == 'read':
                        (data, _) = mySocket.recv(eiotcp._maxrecvfrom) 
                    else:
                        data = None
                except Exception as e:
                    tries += 1
                    if tries > eiotcp.retries: raise TimeoutError
                    sleep(eiotcp.retry_delay)
                else:
                    break
        
        return data
