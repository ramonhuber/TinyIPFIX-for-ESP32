# regular python
import serial
from time import sleep
from tinyIPFIX import TinyIPFIX_Helper_Functions
from tinyIPFIX import Received_Message
# pip install pyzmq
import zmq

class Collector:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        try:
            self.init_serial()
        except:
            print("-------------------------------------------------------")
            print("couldn't connect to serial")
            print("-------------------------------------------------------")
        self.templates = []
        self.zmq_port = "5556"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%s" % self.zmq_port)
        
        
    
    
    def publish(self, record_set):
        helper = TinyIPFIX_Helper_Functions()
        byte_to_send = bytes()
        topic = record_set.set_header.tiny_set_id
        byte_to_send += bytes([topic])
        for field_value in record_set.field_values:
            byte_to_send += field_value
        

        self.socket.send(byte_to_send)
        print(byte_to_send)

        
        
    def init_serial(self):
        port = self.serial_port
        baudrate = 9600
        bytesize=serial.EIGHTBITS
        parity = serial.PARITY_NONE
        stopbits=serial.STOPBITS_ONE
        timeout = 0.2
        xonxoff = 0
        rtscts = 0
        self.ser = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts)
        
    def deinit_serial(self):
        self.ser.close()
        
        
    def read_one_message(self):
        helper = TinyIPFIX_Helper_Functions()
        read = self.ser.read(2)
        if len(read) == 0:
            return None
    
        elif len(read)!=2:
            read_length = len(read)
            read_iterations = 0
            while read_iterations < 100:
                read += self.ser.read(1)
                read_iterations += 1
                read_length = len(read)
                if read_length == 2:
                    break
                sleep(0.05)
            if len(read) != 2:
                print("couldn't read message, message lost, restarting serial")
                self.deinit_serial()
                self.init_serial()
                return None        
            
        length_bitstring = helper.bytes_to_bitstring(read)[6:16]
        length = int(length_bitstring, 2)
        read_iterations = 0
        read_length = len(read)
        while read_iterations < 100:
            read += self.ser.read(length-read_length)
            read_iterations += 1
            read_length = len(read)
            if read_length == length:
                break
            sleep(0.05)
        if len(read) != length:
            print("couldn't read message, message lost, restarting serial")
            self.deinit_serial()
            self.init_serial()
            return None
        read_message = Received_Message(read)
        print ('read message:\n{}\n'.format(read))
        return read_message
            
    def process_read_message(self, read_message):
        message = read_message.parse_message(self.templates)
        if message is None:
            return None
        for record_set in message.records_sets:
            # template record
            if record_set.set_header.tiny_set_id == 2:
                exists_already = 0
                for template in self.templates:   
                    if record_set.template_record.template_record_header.template_id == template.template_record.template_record_header.template_id:
                        exists_already = 1
                        break
                if not exists_already:
                    print('template saved')
                    self.templates.append(record_set)
            
            # data record
            if 128 <= record_set.set_header.tiny_set_id <= 255:
                self.publish(record_set)
                
                
                
        
        
    def run(self, sleep_between_read):
        while True:
            while True:
                read_message = self.read_one_message()
                if read_message is None:
                    break
                self.process_read_message(read_message)
            sleep(sleep_between_read)
    
    
    
serial_port = 'COM5'
my_collector = Collector(serial_port)
my_collector.run(0.1)



