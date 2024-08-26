import serial, time
import os
#from relay_commands import *

SET_ADDRESS_TO_01 = b'\x00\x10\x00\x00\x00\x01\x02\x00\x01\x6a\x00'
READ_DEVICE_ADDRESS_COMMAND = b'\x00\x03\x00\x00\x00\x01\x85\xdb'

TURN_ON_LIST = [
    b'\x01\x05\x00\x00\xff\x00\x8c\x3a',
    b'\x01\x05\x00\x01\xff\x00\xdd\xfa',
    b'\x01\x05\x00\x02\xff\x00\x2d\xfa',
    b'\x01\x05\x00\x03\xff\x00\x7c\x3a',
    b'\x01\x05\x00\x04\xff\x00\xcd\xfb',
    b'\x01\x05\x00\x05\xff\x00\x9c\x3b',
    b'\x01\x05\x00\x06\xff\x00\x6c\x3b',
    b'\x01\x05\x00\x07\xff\x00\x3d\xfb'
]

TURN_OFF_LIST = [
    b'\x01\x05\x00\x00\x00\x00\xcd\xca',
    b'\x01\x05\x00\x01\x00\x00\x9c\x0a',
    b'\x01\x05\x00\x02\x00\x00\x6c\x0a',
    b'\x01\x05\x00\x03\x00\x00\x3d\xca',
    b'\x01\x05\x00\x04\x00\x00\x8c\x0b',
    b'\x01\x05\x00\x05\x00\x00\xdd\xcb',
    b'\x01\x05\x00\x06\x00\x00\x2d\xcb',
    b'\x01\x05\x00\x07\x00\x00\x7c\x0b'
]

READ_RELAY_LIST = [
    b'\x01\x01\x00\x00\x00\x01\xfd\xca',
    b'\x01\x01\x00\x01\x00\x01\xac\x0a',
    b'\x01\x01\x00\x02\x00\x01\x5c\x0a',
    b'\x01\x01\x00\x03\x00\x01\x0d\xca',
    b'\x01\x01\x00\x04\x00\x01\xbc\x0b',
    b'\x01\x01\x00\x05\x00\x01\xed\xcb',
    b'\x01\x01\x00\x06\x00\x01\x1d\xcb',
    b'\x01\x01\x00\x07\x00\x01\x4c\x0b'
]

READ_RELAYS = b'\x01\x01\x00\x00\x00\x08\x3d\xcc'

READ_INPUT = b'\x01\x02\x00\x00\x00\x08\x79\xcc'



class relay:
    def __init__(self,):
        self.ser = None
        self.connected = False

    def begin(self,):
        self.ser = serial.Serial()
        self.connected = False

        if os.path.exists('/dev/ttyACM1'):
            self.ser.port = "/dev/ttyACM1"
            self.connected = True
        elif os.path.exists('/dev/ttyCH343USB1'):
            self.ser.port = "/dev/ttyCH343USB1"
            self.connected = True
        else:
            print('Neither /dev/ttyACM1 nor /dev/ttyCH340USB1 is present')
            self.ser.port = "COM14"
            self.connected = True
            #return False

        #9600,N,8,1
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS    #number of bits per bytes
        self.ser.parity = serial.PARITY_NONE    #set parity check
        self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits

        self.ser.timeout = 0.01                  #non-block read 0.5s
        self.ser.writeTimeout = 0.5             #timeout for write 0.5s
        self.ser.xonxoff = False                #disable software flow control
        self.ser.rtscts = False                 #disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False                 #disable hardware (DSR/DTR) flow control

        try:
            self.ser.open()
        except Exception as ex:
            self.ser.close()
            print ("open serial port error " + str(ex))
            return False
        self.ser.close()
        return True

    def send_command(self,command):
        #begin = time.time()
        self.ser.open()
        if self.ser.isOpen():
            #print("OK")
            try:
                #print(time.time() -begin)
                #self.ser.flushInput() #flush input buffer
                #self.ser.flushOutput() #flush output buffer
                try:
                    self.ser.write(command)
                    time.sleep(0.05)
                except:
                    print("Send command error")
                #read data
                #print(time.time() -begin)
                numofline = 0
                #print("Reading Data:")
                #response = self.ser.readline()
                while True:
                    response = self.ser.readline()
                    #print(response)
                        
                    numofline = numofline + 1
                    if (numofline >= 1):
                        break
                #print(time.time() - begin)
                self.ser.close()
                #print(time.time() - begin)

                return response
            except Exception as e1:
                self.ser.close()
                print ("communicating error " + str(e1))
                return None
        else:
            self.ser.close()
            print ("open serial port error")
            return None
        
    def get_relays_status(self,):
        status = self.send_command(READ_RELAYS)
        # ...
        return status
        

    def get_relay_status(self,relay_num):
        if relay_num >= 0 and relay_num <= 7:
            status = self.send_command(READ_RELAYS)
            print(status)
            inputs = status[3]
            bits = [int(bit) for bit in bin(inputs)[2:].zfill(8)]
            bits.reverse()
            return bits[relay_num]
        else:
            print("Wrong relay_num")
            return -1

    def turn_on_relay(self, relay_num):
        if relay_num >= 0 and relay_num <= 7:
            self.send_command(TURN_ON_LIST[int(relay_num)])
        else:
            print("Wrong relay_num")

    def turn_off_relay(self,relay_num):
        if relay_num >= 0 and relay_num <= 7:
            self.send_command(TURN_OFF_LIST[int(relay_num)])
            return True
        else:
            print("Wrong relay_num")
            return False

    def read_input(self):
        status = self.send_command(READ_INPUT)
        #print(status)
        try:
            inputs = status[3]
            bits = [int(bit) for bit in bin(inputs)[2:].zfill(8)]
            bits.reverse()
        except:
            print("Error during read - trying again")
            self.read_input()
        return bits
