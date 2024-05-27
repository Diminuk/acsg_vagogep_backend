import serial, time
import os
from relay_commands import *
import asyncio
class relay:
    def __init__(self,):
        self.ser = None
        self.connected = False

    def begin(self,):
        self.ser = serial.Serial()

        if os.path.exists('/dev/ttyACM1'):
            self.ser.port = "/dev/ttyACM1"
            self.connected = True
        elif os.path.exists('/dev/ttyCH343USB1'):
            self.ser.port = "/dev/ttyCH343USB1"
            self.connected = True
        else:
            #print('Neither /dev/ttyACM1 nor /dev/ttyCH340USB1 is present')
            #self.connected = False
            
            self.ser.port = "COM14"
            self.connected = True
            #return False

        #9600,N,8,1
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS    #number of bits per bytes
        self.ser.parity = serial.PARITY_NONE    #set parity check
        self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits

        self.ser.timeout = 0.05                  #non-block read 0.5s
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
        self.ser.open()
        time.sleep(0.1)
        if self.ser.isOpen():
            #print("OK")
            try:
                #self.ser.flushInput() #flush input buffer
                #self.ser.flushOutput() #flush output buffer
                #time.sleep(0.1)
                try:
                    self.ser.write(command)
                    time.sleep(0.1)
                except:
                    print("Send command error")
                #read data
                numofline = 0
                #print("Reading Data:")
                while True:
                    response = self.ser.readline()
                    #print(response)
                        
                    numofline = numofline + 1
                    if (numofline >= 1):
                        break
                self.ser.close()
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
        else:
            print("Wrong relay_num")

    def read_input(self):
        status = self.send_command(READ_INPUT)
        print(status)
        print("debug2")
        inputs = status[3]
        print("debug3")
        bits = [int(bit) for bit in bin(inputs)[2:].zfill(8)]
        print("debug4")
        print(bits)
        return bits
