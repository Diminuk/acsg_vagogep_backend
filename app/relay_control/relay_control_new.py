import minimalmodbus as bus
from relay_commands import *
import time
import os
import struct

class relay:
    def __init__(self,):
        self.driver = None
        if os.path.exists('/dev/ttyACM1'):
            self.PORT = "/dev/ttyACM1"
        elif os.path.exists('/dev/ttyCH343USB1'):
            self.PORT = "/dev/ttyCH343USB1"
        else:
            print('Neither /dev/ttyACM1 nor /dev/ttyCH340USB1 is present')
            return False
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = bus.serial.PARITY_NONE
        self.stopbits = 1
        self.timeout = 1
        self.close_port_after_call = True 
        self.clear_buff_before = True
        self.path_param = 409/10e6
    
    def begin(self,):
        self.driver = bus.Instrument(self.PORT, 1, mode=bus.MODE_RTU)
        self.driver.serial.baudrate  = self.baudrate
        self.driver.serial.bytesize  = self.bytesize
        self.driver.serial.parity    = self.parity
        self.driver.serial.stopbits  = self.stopbits
        self.driver.serial.timeout   = self.timeout
        self.driver.close_port_after_each_call = self.close_port_after_call
        self.driver.clear_buffers_before_each_transaction = self.clear_buff_before

    # Function to calculate CRC16
    def calculate_crc(data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return struct.pack('<H', crc)
    
    def build_request(self,address, function_code, register_address, data):
        request = struct.pack('>BBBBBB', address, function_code, register_address >> 8, register_address & 0xFF, data >> 8, data & 0xFF)
        crc = self.calculate_crc(request)
        return request + crc

    def get_relays_status(self,):
        status = self.send_command(READ_RELAYS)
        # ...
        return status

    def turn_on_relay(self, relay_num):
        if relay_num >= 0 and relay_num <= 7:
            request = self.build_request(0x0001, 0x05, 0x0000, 0xFF00)
            response = self.driver.write_read_registers(0x0000, 0xFF00, number_of_registers=1, functioncode=5)
            print("Response:", response)
        else:
            print("Wrong relay_num")

    def turn_off_relay(self,relay_num):
        if relay_num >= 0 and relay_num <= 7:
            self.driver.write_register(0,0,functioncode=0x05)
        else:
            print("Wrong relay_num")

    def read_input(self):
        # status = self.send_command(READ_INPUT)
        # print(status)
        # inputs = status[3]
        # bits = [int(bit) for bit in bin(inputs)[2:].zfill(8)]
        #return bits
        return 