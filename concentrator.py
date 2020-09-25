from device import Device
from tinyIPFIX import *
from time import sleep

class Concentrator(Device):
    
    def __init__(self, device_type, node_number,
             data_measure_interval, template_measure_interval, data_sets_per_message, 
             read_interval, template_sets_per_message, set_size):


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


            

        self.data_measure_interval = data_measure_interval
        self.template_measure_interval = template_measure_interval
        self.data_sets_per_message = data_sets_per_message
        self.read_interval = read_interval
        self.template_sets_per_message = template_sets_per_message
        self.set_size = set_size

        self.data_records_set_list = []
        self.data_records_set_list_length = 0
        self.template_records_set_list = []
        self.template_records_set_list_length = 0


    # if set_size is exceeded or sets_per_message is reached then the sets will be sent
    def run(self):
        
        helper = TinyIPFIX_Helper_Functions()
        template = self.create_template_record_set()
        template_bytes = template.template_records_set_to_byte()
        
        data_i = self.data_measure_interval
        template_i = 0
        read_i = self.read_interval
        
        while True:
            sleep_interval = min(data_i, template_i, read_i)
            sleep(sleep_interval)
                
            template_i -= sleep_interval
            if template_i == 0:
                template_i = self.template_measure_interval
                self.template_records_set_list.append(template_bytes)
                print('created template record: {}\n'.format(template_bytes))
                self.template_records_set_list_length += len(template_bytes)
            
            data_i -= sleep_interval
            if data_i == 0:
                data_i = self.data_measure_interval
                data = self.create_data_records_set()
                data_bytes = data.data_records_set_to_byte()
                self.data_records_set_list.append(data_bytes)
                print('created data record: {}\n'.format(data_bytes))
                self.data_records_set_list_length += len(data_bytes)
            
            read_i -= sleep_interval
            if read_i == 0:
                read_i = self.read_interval
                read = self.read()
                if read is not None:
                    self.buffer_message(read)
                    print('buffered read message: {}\n'.format(read))
            
            if( (len(self.data_records_set_list) >= self.data_sets_per_message) or (self.data_records_set_list_length >= self.set_size) ):
                if len(self.template_records_set_list) > 0:
                    template_message_bytes = helper.aggregate_bytes(0, 0, self.receive_sequence_number(0), *self.template_records_set_list)
                    self.send(template_message_bytes)
                    print('sent template message: {}\n'.format(template_message_bytes))
                    self.template_records_set_list = []
                    self.template_records_set_list_length = 0
                    
                data_message_bytes = helper.aggregate_bytes(0, 0, self.receive_sequence_number(0), *self.data_records_set_list)
                self.send(data_message_bytes)
                print('sent data message: {}\n'.format(data_message_bytes))
                self.data_records_set_list = []
                self.data_records_set_list_length = 0
                
            elif( (len(self.template_records_set_list) >= self.template_sets_per_message) or (self.template_records_set_list_length >= self.set_size) ):
                template_message_bytes = helper.aggregate_bytes(0, 0, self.receive_sequence_number(0), *self.template_records_set_list)
                self.send(template_message_bytes)
                print('sent template message: {}\n'.format(template_message_bytes))
                self.template_records_set_list = []
                self.template_records_set_list_length = 0
                
        