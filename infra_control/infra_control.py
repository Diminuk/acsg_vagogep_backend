import minimalmodbus as bus
import time
import os

class infra:
    def __init__(self,):
        self.driver = None
        # self.PORT = '/dev/ttyUSB0'
        if os.path.exists('/dev/ttyACM1'):
            self.PORT = "/dev/ttyACM1"
        elif os.path.exists('/dev/ttyCH343USB1'):
            self.PORT = "/dev/ttyCH343USB1"
        else:
            print('Neither /dev/ttyACM1 nor /dev/ttyCH340USB1 is present')
            self.PORT = 'COM14'
            #return False
        #self.PORT = 'COM10'
        self.baudrate = 115200
        self.bytesize = 8
        self.parity = bus.serial.PARITY_NONE
        self.stopbits = 2
        self.timeout = 1
        #self.timeout = 1
        self.close_port_after_call = True 
        self.clear_buff_before = True
        self.path_param = 409/10e6
        self.connected = False
    def begin(self,):
        try:
            self.driver = bus.Instrument(self.PORT, 105, mode=bus.MODE_RTU)
            self.driver.serial.baudrate  = self.baudrate
            self.driver.serial.bytesize  = self.bytesize
            self.driver.serial.parity    = self.parity
            self.driver.serial.stopbits  = self.stopbits
            self.driver.serial.timeout   = self.timeout
            self.driver.close_port_after_each_call = self.close_port_after_call
            self.driver.clear_buffers_before_each_transaction = self.clear_buff_before
            self.connected = True
        except Exception as e:
            print(e)
            self.connected = False
            
    def turn_infra(self,value: bool):
        if self.driver is None: 
            print("Driver is not initialized")
            return False 
        if value:
            self.driver.write_register(100,1)
        else:
            self.driver.write_register(100,0)
        return True

    def config_percentage(self,value: int):
        if self.driver is None: 
            print("Driver is not initialized")
            return False 
        if(value >= 92):
            self.driver.write_register(10,92)
        elif value <= 0:
            self.driver.write_register(10,0)
        else:
            self.driver.write_register(10,value)
        return True

