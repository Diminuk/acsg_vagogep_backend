import minimalmodbus as bus
from servo_params import *
import time
import os

class servo:
    def __init__(self,
                 ):
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
        self.timeout = 0.1
        #self.timeout = 1
        self.close_port_after_call = True 
        self.clear_buff_before = True
        self.path_param = 409/10e6
        self.connected = False

    def begin(self,):
        try:
            self.driver = bus.Instrument(self.PORT, 127, mode=bus.MODE_RTU)
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
  
    def change_path_param(self,param):
        self.path_param = param
        print(f"Path param changed to: {self.path_param}")
        
    def read_16_bit():
        pass 

    def read_32_bit(self,address):
        if self.driver is None:
            print("Driver not initialized")
            return False
        def combine_to_32(high, low):
            combined_data = (high << 16) | low
            return combined_data
        try:
            data = self.driver.read_registers(address,2,3)
        except:
            print("Error during read registers")
            return False
        return combine_to_32(data[1],data[0])
        
        
    def config_path_def(self,
                        path_num,
                        spd_num,
                        dly_num,
                        auto_num,
                        type_num,
                        #opt_num,
                        acc_num,
                        dec_num
                        ):
        if self.driver is None: 
            print("Driver is not initialized")
            return False 
        if path_num > 49 or path_num < 1:
            print("Wrong path number")
            return False 
        if spd_num > 15 or spd_num < 0:
            print("Wrong speed num")
            return False 
        if dly_num > 15 or dly_num < 0:
            print("Wrong delay num")
            return False 
        if acc_num > 15 or acc_num < 0:
            print("Wrong acc num")
            return False 
        if dec_num > 15 or dec_num < 0:
            print("Wrong dec num")
            return False 
        if auto_num not in [0,1]:
            print("Wrong auto mode num")
            return False
        if type_num not in [1,2]: # 1: speed , 2: single position
            print("Wrong type num")
            return False
        #if opt_num not in [1,2]:
        #    print("Wrong opt num")
        #    return False
        
        # write register
        try:
            self.driver.write_registers(int("0x0604",16),[int(f"0x{HEXA_MAP[dec_num]}{HEXA_MAP[acc_num]}5{type_num}",16),int(f"0x0{auto_num}{HEXA_MAP[dly_num]}{HEXA_MAP[spd_num]}",16)]) # LOW | HIGH
        except:
            print("Error during writing registers on path define")
            return False
        
        # read register for double check
        check_data = self.read_32_bit(int("0x0604",16))
        print(check_data)
        # implement check later
        return True

    def config_path_data(self,path_num,length):
        # length: mm with sign (can be float)
        if self.driver is None: 
            print("Driver has not been initialized")
            return False
        
        if path_num > 49 or path_num < 1:
            print("Invalid path number")
            return False
        
        converted = int(length / self.path_param)
        print(length)
        print(converted)

        if(converted < -214783648 or converted > 214783648):
            print("WRITE ERROR - Too large input value")
            return False 
        high_word = (converted >> 16) & 0xFFFF

        # Extracting the low word (last 16 bits)
        low_word = converted & 0xFFFF

        print("High word:", hex(high_word))
        print("Low word:", hex(low_word))

        try:
            self.driver.write_registers(1542 + (path_num-1)*4,[low_word,high_word])
        except:
            print("Error during write")
            return False
        # check 
        new_path_data = self.read_32_bit(1542 + (path_num-1)*4)
        print(f"New data on 0x{1542 + (path_num-1)*4:04x} : {new_path_data}")

        if new_path_data == converted:
            print("Write success")
            return True 
        else: 
            print("Write error")
            return False

    def start_path(self,path_num):
        if ((path_num > 0 and path_num < 50) or path_num == 1000):
            self.driver.write_register(int("0x050e",16),path_num)
            print(f"Start path {path_num}")
        else: 
            print("Path number exceeds limit")

    def stop_path(self):
        self.driver.write_register(int("0x050e",16),1000)
        print("Path stopped")

    def get_do_status(self):
        status = self.driver.read_registers(int("0x0412",16),1,3) # 1542 -->> P6.003
        binary_representation = bin(status[0])[2:].zfill(6)
        return binary_representation
    
    def poll_eop(self):
        return self.get_do_status()[2]

    def get_axis_pos(self):
        self.driver.write_register(int("0x0062",16),int("0x0001",16))
        print(self.read_32_bit(104))
        return self.read_32_bit(104)

    def zero_pos(self):
        print(self.driver.read_register(int("0x0210",16)))
        self.driver.write_register(int("0x0210",16),271)
        print(self.driver.read_register(int("0x028a",16)))
        self.driver.write_register(int("0x028a",16),int("0x0000",16))
        print("..")
        #self.driver.write_register(654,1)
        #self.driver.write_register(int("0x028e",16),int("0x0000",16))

    def get_path_def(self,path_num):
        pass

    def get_paths_def(self):
        pass

    def get_path_data(self,path_num):
        pass

    def get_paths_data(self):
        pass

    # Table functions
    def change_speed_table(self):
        pass

    def change_delay_table(self):
        pass

    def change_acc_table(self):
        pass

    def change_dec_table(self):
        pass

    def get_speed_table(self):
        pass
    
    def get_delay_table(self):
        pass
    
    def get_acc_table(self):
        pass
    
    def get_dec_table(self):
        pass
    
    