# EtherIO

Python driver for Elexol EtherIO devices

## Description

This driver provides a higher level abstraction of the Elexol IO device access through use of object dot notation.

The Elexol EtherIO devices provide access to digital IOs through a network ethernet interface. Each device is divided into a set of 8-bit ports that can be defined as input or output on a bit by bit basis.

After creating a device object, device and port attributes can be accessed through simple dot notation both for reading and assignment.

A device object is composed of:

* dev  
  * .io[n]   
  * .porta (portb, portc, ...)  
    * .val  
    * .dir

### Code Use

* import the module (eio.py)
* create a device object
* set up ports as needed
* write and read port values
```
from eio import *

dev = eio24r("192.168.1.10")
print(dev)
dev.reset()
dev.porta.dir = PORTDIROUTPUT
dev.portb.dir = PORTDIRINPUT

dev.porta.val = 0x55   # send output to port a
v = dev.portb.val      # read value from port b
```

There is a demo python script (eiodemo.py) which can show patterns on a port if an LED board is connected to the port connector.

loopbacktest() also included in the demo script performs a write-read-verify test when portb and portc are looped together with a 10-pin cable. This is a good test of the board and your network performance as statistics are collected on the underlying udp driver.


## Help

Most class and functions provide a help doc string through the python help() function.  This documentation is not meant as a thorough explanation of the the Elexol device usage, please refer to their website and part documentation, links provided below. Electronics knowledge is strongly recommended if you are using these devices to interface to other hardware and electronics.
```
help(eio24r)  #help on an EIO24R type module
help(eio24t)  #help on an EIO24 TCP type module
help(eio72t)  #help on an EIO72 TCP type module

help(dev)     #once the device has been defined this should provide the device specific help
```

## Resource links

- [Elexol Website](https://temperosystems.com.au/shop/?fwp_tempero_systems=i-o-controllers)
- [IO24R Module](https://temperosystems.com.au/products/ether-io24-r/)
  - [Manual](https://temperosystems.com.au/wp-content/uploads/2020/04/EtherIO24R_UM1-data-sheet-tempero.pdf)
- [IO24 TCP Module](https://temperosystems.com.au/products/ether-io24-tcp/)
  - [Manual](https://temperosystems.com.au/wp-content/uploads/2020/04/EtherIO24TCPDS.pdf)
- [IO72 TCP Module](https://temperosystems.com.au/products/ether-io72-tcp/)
  - [Manual](https://temperosystems.com.au/wp-content/uploads/2020/04/EtherIO72TCPDS.pdf)
- [LED Module](https://temperosystems.com.au/products/connector-led-board/)
- [Switch/Pushbutton Board](https://temperosystems.com.au/products/switch-push-button-board/)

Elexol provides tools to manage device setup and setting of boot features. See their respective device resource pages.   

Also, a reseller:
[Salig](https://www.saelig.com/category/IO.htm)

## Author

Steven Herbold  
loopgain-etherio@yahoo.com

## Version History

* 0.0 Initial Release

## License

This project is licensed under the MIT License - see the LICENSE file for details

## More details

This driver was written as an exercise to learn python class attributes, especially of a type that require contacting a remote device for their actual value. 

### UDP driver

This driver makes use of UDP packets to send and receive data from the modules. UDP protocol does not guarantee delivery so some retries are incorporated into the driver.
The driver does a write-read-verify for the port registers, and if verify fails, attempts a write retry. This can be disabled by setting eioudp.write_validate to False.
Retry count, inter-retry delay, timeout can be adjusted in the eioudp class. Current settings seem to work well over my WiFi network but you can increase them if you are finding TimeoutError exceptions. The eioudp class also maintains some statistics on commands sent and retry events. These can be returned with eioudp.stats(), and cleared with eioudp.stats_clear().

### Module Command Differences

This driver makes use of of legacy supported commands for the IO24/IO72 TCP modules to create a common base for all the modules. There is a connection oriented (TCP) protocol for the newer modules that is probably more reliable, but not supported on the older IO24R module. I have included an eiotcp class driver, but this is not tested or used.

### Aditional Device Object Attributes

* .eeprom_ipaddr    get or set the device ip address
* .eeprom_ipmask    get or set the device ip mask
* .eeprom_ipgway    get or set the device ip gateway

These attibutes are provided as an example of setting the eeprom boot values. They are typically set using the manufacturer tools.
The device can be set to a fixed ip address using the jumpers, and from there configured to boot to the desired address.

## Conclusion

Let me know if this has been useful or helpful in your development. 
Also looking for suggestions and recommendations to make this more Pythonic in style.
