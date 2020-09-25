from device import Device
from tinyIPFIX import *
from time import sleep
import machine
import ujson
from machine import RTC


class End_Device(Device):
    def __init__(self, device_type, node_number,
                 data_measure_interval, template_measure_interval, data_sets_per_message):
        
        if(machine.reset_cause() == machine.DEEPSLEEP_RESET):
            f = open("variables.json", "r")
            self.variable_dict = ujson.loads(f.read())
            f.close()
            self.sequence_number = self.variable_dict["sequence_number"]
            self.node_number = node_number
            self.rtc = RTC()
            
            if (device_type == 'esp32'):
                self.tx = 17
                self.rx = 16
            elif (device_type == 'superb'):
                self.tx = 32
                self.rx = 33
            else:
                raise Exception("Device Type not known")
            

            self.data_measure_interval = data_measure_interval
            self.template_measure_interval = template_measure_interval
            self.data_sets_per_message = data_sets_per_message
            self.data_records_set_list = self.variable_dict["data_records_set_list"]
  
        else:
            self.set_clock()
            self.sequence_number = 0
            self.node_number = node_number

            if (device_type == 'esp32'):
                self.tx = 17
                self.rx = 16
            elif (device_type == 'superb'):
                self.tx = 32
                self.rx = 33
            else:
                raise Exception("Device Type not known")
            
            self.variable_dict = {}
            self.data_measure_interval = data_measure_interval
            self.template_measure_interval = template_measure_interval
            self.data_sets_per_message = data_sets_per_message
            self.variable_dict["template_i"] = 0
            self.variable_dict["data_i"] = data_measure_interval
            self.variable_dict["data_records_set_list"] = []
                
    
    # data and template sleep in seconds
    def run(self):
        helper = TinyIPFIX_Helper_Functions()
        template_rec_set = self.create_template_record_set()
        template_i = self.variable_dict["template_i"]
        data_i = self.variable_dict["data_i"]
        set_list = self.variable_dict["data_records_set_list"]
        self.data_records_set_list = []
        for s in set_list:
            self.data_records_set_list.append(bytes(s, 'utf-8'))
        
        # to correct timing (actually data and template are sent less ofthen than sleep time):
        # -> t = time.time()
        # -> elapsed = time.time() - t
        # alternative method would be to calculate sleeptime every time instead of using gcd
        while True:
            if template_i == 0:
                template_i = self.template_measure_interval
                template_to_send = self.create_template_message(template_rec_set)
                self.send(template_to_send)
                print('sent template message: {}\n'.format(template_to_send))
            if data_i == 0:
                data_i = self.data_measure_interval
                data_bytes = self.create_data_records_set().data_records_set_to_byte()
                self.data_records_set_list.append(data_bytes)
                print('created data record: {}\n'.format(data_bytes))
                if len(self.data_records_set_list) >= self.data_sets_per_message:
                    data_message_bytes = helper.aggregate_bytes(0, 0, self.receive_sequence_number(0), *self.data_records_set_list)
                    self.send(data_message_bytes)
                    print('sent data message: {}\n'.format(data_message_bytes))
                    self.data_records_set_list = []
                    
            sleep_time = min(data_i, template_i)
            template_i -= sleep_time
            data_i -= sleep_time

            self.variable_dict["template_i"] = template_i
            self.variable_dict["data_i"] = data_i
            self.variable_dict["data_records_set_list"] = self.data_records_set_list
            self.variable_dict["sequence_number"] = self.sequence_number
            f = open("variables.json", "w")
            f.write(ujson.dumps(self.variable_dict))
            f.close()
            print(self.sequence_number)
            machine.deepsleep(sleep_time*1000)
            
    