from machine import UART, Pin, RTC
import network
import ntptime
import ustruct
from time import sleep
from tinyIPFIX import *

class Device:
    def __init__():
        pass

    def set_clock(self):
        clock=(2017, 8, 23, 1, 08, 00, 0, 0)
        self.rtc = RTC()
        self.rtc.datetime(clock) # (year, month, day, weekday, hours, minutes, seconds, subseconds)
        
        # set time
        """
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        ssid_list = wlan.scan()
        success = 0
        for ssid in ssid_list:
            if ssid[0].decode("utf-8") == 'Androidmon':
                wlan.connect('Androidmon', 'uubs5894223dzG*o')
                for i in range(10):
                    if wlan.isconnected():
                        break
                    sleep(0.5)
                if wlan.isconnected():
                    ntptime.settime()
                    # settng time to swiss time could make it go off some fractions of a second
                    t = self.rtc.datetime()
                    adjusted_time_switzerland = (t[0], t[1], t[2], t[3], t[4]+2, t[5], t[6], t[7])
                    self.rtc.datetime(adjusted_time_switzerland)
                    success = 1 
                break
        wlan.active(False)
        if success == 0:
            raise Exception("could not update time because there is no internet connection")
        """    
    
    def run(self):
        pass
        
    def __connect_uart(self):
        uart = UART(1, baudrate=9600, rx=self.rx, tx=self.tx)
        self.uart = uart
        
    def __disconnect_uart(self):
        self.uart.deinit()
        
    def send(self, send):
        try:
            self.uart.write(send)
        except:
            self.__connect_uart()
            self.uart.write(send)
            
    def read(self):
        try:
            val = self.uart.read()
        except:
            self.__connect_uart()
            val = self.uart.read()
        return val
    
    def sensor_best_wlan(self):
        try:
            self.wlan.active(True)
        except:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
        available_wlans = self.wlan.scan()
        self.wlan.active(False)
        ssid = available_wlans[0][0]
        max_rssi = available_wlans[0][3]
        for wlan in available_wlans:
            if(wlan[3] > max_rssi):
                max_rssi = wlan[3]
                ssid = wlan[0]
        return ssid.decode("utf-8")
    
    def sensor_is_cable_connected(self):
        p1 = Pin(18, Pin.IN, Pin.PULL_DOWN)
        return p1.value()
    
    def sensor_get_timestamp(self):
        timestamp = ""
        t = self.rtc.datetime()
        timestamp += "0" * (4 - len(str(t[0]))) + str(t[0]) + "-" #year[0:4]
        timestamp += "0" * (2 - len(str(t[1]))) + str(t[1]) + "-" #month[5:7]
        timestamp += "0" * (2 - len(str(t[2]))) + str(t[2]) + "-" #day [8:10]
        timestamp += "0" * (2 - len(str(t[4]))) + str(t[4]) + "-" #hour [11:13]
        timestamp += "0" * (2 - len(str(t[5]))) + str(t[5]) + "-" #minute [14:16]
        timestamp += "0" * (2 - len(str(t[6]))) + str(t[6])       #second [17:19]
        return timestamp
    
    def sensor_temperature(self, hour = 18, minute = 0):
        timestamp = self.sensor_get_timestamp()
        hour = int(timestamp[11:13], 10)
        minute = int(timestamp[14:16], 10)
        # list holding temperatures of Wednesday 22.07.2020, first entry is temperature at 00:00, last at 23:00
        temps = [21.1,20,18.8,18.5,18.1,17.8,17.6,18.5,19,19.8,
                21.1,22.3,23.8,25.2,26.5,27.7,27.3,27.5,27,26.1,
                25,23.9,22.7,21.5]
        if 0 <= hour <= 22:
            return (60-minute)/60*temps[hour] + minute/60*temps[hour+1]
        return None
    
    def receive_sequence_number(self, e2):
        s = self.sequence_number
        if self.sequence_number == 255 and e2 == 0:
            self.sequence_number = 0
        elif self.sequence_number == 65535 and e2 == 1:
            self.sequence_number = 0
        else:
            self.sequence_number += 1
        return s
    
    # add bytes object, representing one or many TinyIPFIX messages, to the buffer
    def buffer_message(self, messages_bytes):
        helper = TinyIPFIX_Helper_Functions()
        #for message in messages_bytes:
        msg_list = helper.message_bytes_to_list_of_message_bytes(messages_bytes)
        for msg in msg_list:
            record_set = helper.message_bytes_to_records_set_bytes(msg)
            msg_type = helper.template_or_data_records_set(record_set)
            if (msg_type == 'template'):
                self.template_records_set_list.append(record_set)
                self.template_records_set_list_length += len(record_set)
            elif (msg_type == 'data'):
                self.data_records_set_list.append(record_set)
                self.data_records_set_list_length += len(record_set)
    
    # needs to be adjusted for each device
    def create_template_record_set(self):
        # Following comments describe our custom information elements
        # ElementID; Name; Abstract Data Type; Data Type Semantics; Status; Description; Units; Range
        # 1; Source of Value; unsigned16; ; current; Identifies the Node the Measured Value is comming from (Unique Node number with Range [0, 65535]);;
        # 2; Humidity; float32; ; current; (measured by sensor_temperature()) Represents a Humidity Value sensed with the ExampleManufacturer S1 sensor;;
        # 3; Date and Time of measurement; string; ; current; current time and date of measurement measured by sensor_get_timestamp();;

        # create field specifier 1 - Node Number
        enterprise_bit = 1
        information_element_identifier = 1
        field_length = 2
        enterprise_number = 2882382797
        field_specifier1 = Field_Specifier(enterprise_bit, information_element_identifier, field_length, enterprise_number)

        # create field specifier 2 - humidity
        enterprise_bit = 1
        information_element_identifier = 2
        field_length = 4
        enterprise_number = 2882382797
        field_specifier2 = Field_Specifier(enterprise_bit, information_element_identifier, field_length, enterprise_number)

        # create field specifier 3 - timestamp
        enterprise_bit = 1
        information_element_identifier = 3
        field_length = 19
        enterprise_number = 2882382797
        field_specifier3 = Field_Specifier(enterprise_bit, information_element_identifier, field_length, enterprise_number)

        # create template record
        template_id = 128
        template_record = Template_Record(template_id, field_specifier1, field_specifier2, field_specifier3)

        # create template record set
        template_record_set1 = Template_Records_Set(template_record)
        
        return template_record_set1
    
    def create_template_message(self, *template_record_sets):
        # create (template) message
        e1 = 0
        e2 = 0
        sequence_number = self.receive_sequence_number(0)
        message = Message(e1, e2, sequence_number, *template_record_sets)
        template_message_bytes = message.message_to_byte()

        return template_message_bytes
    
    # needs to be adjusted for each device
    def create_data_records_set(self):
        field_value_1 = ustruct.pack('>H', self.node_number) # unsigned16 Range [0, 65535]
        field_value_2 = ustruct.pack('>f', 46) # float32, for reverse do: ustruct.unpack('>f', field_value)[0]
        field_value_3 = self.sensor_get_timestamp().encode("utf-8") # string with length 19
        tiny_set_id = 128
        data_records_set = Data_Records_Set(tiny_set_id, field_value_1, field_value_2, field_value_3)
        return data_records_set

    def create_data_message(self, data_records_set_list): 
        e1 = 0
        e2 = 0
        sequence_number = self.receive_sequence_number(0)
        data_message = Message(e1, e2, sequence_number, *data_records_set_list)
        data_message_bytes = data_message.message_to_byte()
        return data_message_bytes
    