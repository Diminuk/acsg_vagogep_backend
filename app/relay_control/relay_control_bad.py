import minimalmodbus as bus
import os
from relay_commands import *
import time

class relay:
    def __init__(self):
        self.instrument = None

    def begin_relay_serial(self):
        if os.path.exists('/dev/ttyACM1'):
            port = "/dev/ttyACM1"
        elif os.path.exists('/dev/ttyCH343USB1'):
            port = "/dev/ttyCH343USB1"
        else:
            print('Neither /dev/ttyACM1 nor /dev/ttyCH340USB1 is present')
            return False

        try:
            self.instrument = bus.Instrument(port, 1,mode=bus.MODE_RTU)  # Port name, slave address (in decimal)
            self.instrument.serial.baudrate = 9600
            self.instrument.serial.bytesize = 8
            self.instrument.serial.parity = bus.serial.PARITY_NONE
            self.instrument.serial.stopbits = 1
            self.instrument.serial.timeout = 0.5  # 0.5 second timeout for both read and write
            self.instrument.close_port_after_each_call =True
            self.instrument.clear_buffers_before_each_transaction = True
        except Exception as ex:
            print("Failed to initialize relay:", ex)
            return False

        return True

    def send_command(self, command):
        try:
            if not self.instrument:
                print("Serial port is not initialized. Please call begin_relay_serial() first.")
                return None


            print("Serial port opened successfully.")
            try:
                # Flush input and output buffers
                #self.instrument.serial.flushInput()
                #self.instrument.serial.flushOutput()
                #time.sleep(0.1)

                # Write the command
                self.instrument.write_register(command, 0)

                # Read data
                response = self.instrument.read_register(command, 1)

                print("Received response:", response)
                return response
            except Exception as e:
                print("Error while sending command:", e)
                return None
        except Exception as ex:
            print("An error occurred:", ex)
            return None
        
    def get_relay_status(self, relay_num):
        if 0 <= relay_num <= 7:
            status = self.send_command(READ_RELAYS)
            if status is not None:
                byte_with_ff = status[0]  # Assuming the byte with \xff is at position 0
                # Convert byte to binary representation
                binary_representation = bin(byte_with_ff)[2:].zfill(8)
                # Access individual bits like an array
                bit_array = [int(bit) for bit in binary_representation[::-1]]  # Reverse the bit order
                print(bit_array)
                print(bit_array[relay_num])
                return bit_array[relay_num]
            else:
                print("Failed to get relay status")
                return -1
        else:
            print("Wrong relay_num")
            return -1
    
    def get_relay_status(self,relay_num):
        if relay_num >= 0 and relay_num <= 7:
            status = self.send_command(READ_RELAYS)
            byte_with_ff = status[3]
            # Convert byte to binary representation
            binary_representation = bin(byte_with_ff)[2:].zfill(8)
            # Access individual bits like an array
            bit_array = [int(bit) for bit in binary_representation].reverse()
            print(bit_array)
            print(bit_array[relay_num])
            return bit_array[relay_num]
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
        inputs = status[3]
        bits = [int(bit) for bit in bin(inputs)[2:].zfill(8)]
        return bits