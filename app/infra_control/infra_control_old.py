import serial
import time
import os

class infra:
    def __init__(self) -> None:
        self.ser = None
        self.connected = False
    
    def begin(self):
        self.ser = serial.Serial()

        if os.path.exists('/dev/ttyACM1'):
            self.ser.port = "/dev/ttyACM1"
            self.connected = True
        elif os.path.exists('/dev/ttyCH343USB1'):
            self.ser.port = "/dev/ttyCH343USB1"
            self.connected = True
        else:
            #print('Neither /dev/ttyACM1 nor /dev/ttyCH340USB1 is present')
            self.ser.port = "COM14"
            self.connected = True
            #self.connected = False
            #return False
        
        #self.ser.port = 'COM10'
        
        self.ser.baudrate = 115200
        self.ser.timeout = 0.5

        try:
            self.ser.open()
        except Exception as ex:
            self.ser.close()
            print ("open serial port error " + str(ex))
            return False
        self.ser.close()
        return True

    def send_data(self,command):
        if self.ser is None:
            print("Infra comm has'nt been started")
            return False
        try:
            if self.ser.isOpen():
                try:
                    self.ser.write(command)
                    time.sleep(0.05)
                except:
                    print("Error during infra write")
        except:
            print(f"Exception during writing to serial (Infra)")
            return False
        return True

    def receive_data(self):
        if self.ser is None:
            print("Infra has'nt been started")
            return None 
        try:
            self.ser.open()
        except:
            print("Error during infra receive data")
            self.ser.close()
            return None
        data = self.ser.read(32)
        self.ser.close()
        return data

    def config_percentage(self,value: int):
        WAIT_RESPONSE = False
        if not 0 <= value <= 100:
            print("Value must be between 0 and 100")
        self.ser.open()
        time.sleep(0.1)
        low_byte = value & 0xFF
        high_byte = (value >> 8) & 0xFF
        command = b'\x69\x00\x00\x00\x06\x00' + bytes([low_byte]) + bytes([high_byte])
        tmp_time = time.time()
        if self.ser.isOpen():
            self.ser.write(command)
            time.sleep(0.05)
        else:
            print("Serial is'nt open")
        #self.send_data(command)
        #time.sleep(0.1)
        print(f"Send Infra config percentage data ex. time: {time.time() - tmp_time}")
        tmp_time = time.time()
        #response = self.ser.read(32)
        if(WAIT_RESPONSE):
            numofline = 0
            while True:
                response = self.ser.readline()
                print(response)
                    
                numofline = numofline + 1
                if (numofline >= 1):
                    break
            print(f"Receive Infra config percentage data response ex. time: {time.time() - tmp_time}")
            self.ser.close()
            if response is None:
                print("Response was None")
            response_bytes = bytes.fromhex(response.decode('utf-8').replace('\\x', '').replace('\n',''))
            last_bytes = response_bytes[-2:]
            integer_value = int.from_bytes(last_bytes, byteorder='big', signed=False)
            if integer_value != value:
                print(f"Wrong response: expected value:{value} received value:{integer_value}")
        else:
            self.ser.close()

    def get_percentage(self):
        command = b'\x69\x00\x00\x00\x03\x00\x00\x00'
        self.ser.open()
        print(self.ser.isOpen())
        self.send_data(command)
        time.sleep(0.1)
        #response = self.ser.read(32)
        numofline = 0
        while True:
            response = self.ser.readline()
            #print(response)
                
            numofline = numofline + 1
            if (numofline >= 1):
                break
        print(response)
        self.ser.close()
        if response is None:
            print("Response was None")                                                
        response_bytes = bytes.fromhex(response.decode('utf-8').replace('\\x', '').replace('\n',''))
        last_bytes = response_bytes[-2:]
        integer_value = int.from_bytes(last_bytes, byteorder='little', signed=False)
        return integer_value 

    def turn_infra(self,value: bool):
        WAIT_RESPONSE = False
        tmp_time = time.time()
        if value:
            command = b'\x69\x00\x01\x00\x06\x00\x01\x00'
        else: 
            command = b'\x69\x00\x01\x00\x06\x00\x00\x00'
        self.ser.open()
        print(f"Time until ser open: {time.time()-tmp_time}")
        tmp_time = time.time()
        if self.ser.isOpen():
            self.ser.write(command)
            #time.sleep(0.1)
        else:
            print("Serial is'nt open")
        #response = self.ser.read(32)
        if WAIT_RESPONSE:
            numofline = 0
            while True:
                response = self.ser.readline()
                print(response)
                    
                numofline = numofline + 1
                if (numofline >= 1):
                    break
            self.ser.close()
            print(f"Time until read response: {time.time()-tmp_time}")
            tmp_time = time.time()
            #print(response)
            if response is None:
                raise ValueError("Response was None")
            response_bytes = bytes.fromhex(response.decode('utf-8').replace('\\x', '').replace('\n',''))
            last_bytes = response_bytes[-2:]
            integer_value = int.from_bytes(last_bytes, byteorder='big', signed=False)
            if integer_value == 1:
                tmp =  True
            elif integer_value == 0:
                tmp = False 
            else:
                raise ValueError("Response was invalid")
            #if value != tmp:
            #    raise ValueError("Write error, response/value mismatch")
            return integer_value
        else:
            self.ser.close()
            return 0



    def get_infra(self):
        command = b'\x69\x00\x01\x00\x03\x00\x00\x00'
        self.ser.open()
        self.send_data(command)
        time.sleep(0.1)
        response = self.ser.read(32)
        print(response)
        self.ser.close()
        if response is None:
            raise ValueError("Response was None")                                                
        response_bytes = bytes.fromhex(response.decode('utf-8').replace('\\x', ''))
        last_bytes = response_bytes[-2:]
        integer_value = int.from_bytes(last_bytes, byteorder='little', signed=False)
        return integer_value 
    
    def get_temp(self):
        command = b'\x69\x00\x02\x00\x03\x00\x00\x00'
        self.ser.open()
        self.send_data(command)
        time.sleep(0.1)
        response = self.ser.read(32)
        self.ser.close()
        if response is None:
            raise ValueError("Response was None")                                                
        response_bytes = bytes.fromhex(response.decode('utf-8').replace('\\x', ''))
        last_bytes = response_bytes[-2:]
        integer_value = int.from_bytes(last_bytes, byteorder='little', signed=False)
        return integer_value 
