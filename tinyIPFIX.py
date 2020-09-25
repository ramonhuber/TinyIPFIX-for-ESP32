class TinyIPFIX_Helper_Functions:
    # converts a message field to a bitstring (use bytes_to_bitstring for other bytes objects)
    def field_to_bitstring(self, field, field_width):
        if isinstance(field, bytes):
            s = str(field)[2:]
        else:
            s = str(bin(field))[2:]
        if len(s) <= field_width:
            return ("0" * (field_width - len(s))) + s
        else:
            raise Exception("Field Value is too long to fit into field")
        
    def bitstring_to_bytes(self, s):
        return int(s, 2).to_bytes(len(s) // 8, 'big')
    
    # converts bytes object (in hex) to string of bits
    def bytes_to_bitstring(self, bytes_object):
            if not isinstance(bytes_object, bytes):
                raise Exception("not a bytes object")
            bitstring = ""
            for byte in bytes_object:
                bitstring += ("0" * (8 - len(str(bin(byte))[2:]))) + str(bin(byte))[2:]
            return bitstring
    
    # takes a template_id and return a list of the field lengths (in bytes) of the fields
    def template_id_to_field_length(self, template_id):
        lengths = []
        lengths.append()
        if template_id == 128:
            pass

    def template_or_data_message_byte(self, message):
        msg = self.bytes_to_bitstring(message)
        e1 = int(msg[0:1], 2)
        e2 = int(msg[1:2], 2)
        if e1==0 and e2==0:
            first_tiny_setid = int(msg[24:32], 2)
            first_set_start = 3
        elif (e1==0 and e2==1) or (e1==1 and e2==0):
            first_tiny_setid = int(msg[32:40], 2)
            first_set_start = 4
        else:
            first_tiny_setid = int(msg[40:48], 2)
            first_set_start = 5
        # first tiny_set_id marks the first byte that contains a set (-> depends on length of header)
        # template sets
        if first_tiny_setid == 2:            
            return ('template', first_set_start)
        # data sets
        if 128 <= first_tiny_setid <= 255:
            return ('data', first_set_start)
    
    def template_or_data_records_set(self, message):
        if type(message) is bytes:
            message = self.bytes_to_bitstring(message)
        if int(message[0:8], 2) == 2:
            return 'template'
        if 128 <= int(message[0:8], 2) <= 255:
            return 'data'
    
    # takes a bytes object and return a list of bytes object, each entry representing one TinyIPFIX message
    def message_bytes_to_list_of_message_bytes(self, message):
        pos = 0
        msg_list = []
        total_length = len(message)
        while pos<total_length:
            #assert(pos+1 < total_length), "message is incomplete"
            if not(pos+1 < total_length):
                print('message is incomplete, message lost')
                break
            length = int(self.bytes_to_bitstring(message[pos:pos+2])[6:16], 2)
            #assert(pos+length <= total_length), "message is incomplete"
            if not(pos+length <= total_length):
                print('message is incomplete, message lost')
                break
            msg_list.append(message[pos:pos+length])
            pos+=length
        return msg_list
    
    def message_bytes_to_records_set_bytes(self, message):
        msg = self.bytes_to_bitstring(message)
        e1 = int(msg[0:1], 2)
        e2 = int(msg[1:2], 2)
        if e1==0 and e2==0:
            return message[3:]
        elif (e1==0 and e2==1) or (e1==1 and e2==0):
            return message[4:]
        elif (e1==1 and e2==1):
            return message[5:]
        else:
            raise Exception("E1 or E2 is neither 0 nor 1")
    
    # takes records_sets bytes and return one message_bytes
    def aggregate_bytes(self, e1, e2, sequence_number, *record_sets):
        prev_msg_type = None
        set_byte = bytes()
        for record_set in record_sets:
            record_set_type = self.template_or_data_records_set(record_set)
            assert(record_set_type == prev_msg_type or prev_msg_type == None), "cannot mix template and data sets while ating"
            prev_msg_type = record_set_type
            set_byte += record_set
        tot_set_length = len(set_byte)
            
        set_id_lookup = 0
        header_byte = ""
        header_byte += self.field_to_bitstring(e1, 1)
        header_byte += self.field_to_bitstring(e2, 1)
        header_byte += self.field_to_bitstring(set_id_lookup, 4)
        if(e2 == 0 and e1 == 0):
            header_byte += self.field_to_bitstring(3+tot_set_length, 10)
        elif((e2==1 and e1==0) or (e2==0 and e1==1)):
            header_byte += self.field_to_bitstring(4+tot_set_length, 10)
        else:
            header_byte += self.field_to_bitstring(5+tot_set_length, 10)
        if e2 == 1:
            header_byte += self.field_to_bitstring(sequence_number, 16)
        else:
            header_byte += self.field_to_bitstring(sequence_number, 8)
        if e1 == 1:
            extended_set_id = 0
            header_byte += self.field_to_bitstring(extended_set_id, 8)
        header_byte = self.bitstring_to_bytes(header_byte)
        return header_byte+set_byte
        
class Message_Header:
    def __init__(self, e1, e2, sequence_number, length):
        self.e1 = e1
        self.e2 = e2
        self.set_id_lookup = 0
        self.length = length
        if (e2 == 1):
            self.extended_sequence_number = sequence_number
        else:
            self.sequence_number = sequence_number
        if (e1 == 1):
            self.extended_set_id = 0

class Set_Header:
    def __init__(self, tiny_set_id, length):
        self.tiny_set_id = tiny_set_id
        self.length = length

class Template_Record_Header:
    def __init__(self, template_id, field_count):
        self.template_id = template_id
        self.field_count = field_count

class Field_Specifier:
    def __init__(self, enterprise_bit, information_element_identifier, field_length, enterprise_number = None):
        self.enterprise_bit = enterprise_bit
        self.information_element_identifier = information_element_identifier
        self.field_length = field_length
        if(enterprise_bit == 1): # and enterprise_number is not None
            self.enterprise_number = enterprise_number
    def get_length(self):
        if(self.enterprise_bit == 0):
            return 3
        else:
            return 7
            
class Template_Record:
    def __init__(self, template_id, *field_specifiers):
        self.template_record_header = Template_Record_Header(template_id, len(field_specifiers))
        self.field_specifiers = field_specifiers
    def get_length(self):
        length = 0
        for fs in self.field_specifiers:
            length += fs.get_length()
        return length + 2

class Template_Records_Set:
    def __init__(self, template_record):
        self.set_header = Set_Header(2, template_record.get_length() + 2)
        self.template_record = template_record
        
    def template_records_set_to_byte(self):
        helper = TinyIPFIX_Helper_Functions()
        bitstring = ""
        bitstring += helper.field_to_bitstring(self.set_header.tiny_set_id, 8)
        bitstring += helper.field_to_bitstring(self.set_header.length, 8)
        bitstring += helper.field_to_bitstring(self.template_record.template_record_header.template_id, 8)
        bitstring += helper.field_to_bitstring(self.template_record.template_record_header.field_count, 8)
        for field_spec in self.template_record.field_specifiers:
            bitstring += helper.field_to_bitstring(field_spec.enterprise_bit, 1)
            bitstring += helper.field_to_bitstring(field_spec.information_element_identifier, 15)
            bitstring += helper.field_to_bitstring(field_spec.field_length, 8)
            if field_spec.enterprise_bit == 1:
                bitstring += helper.field_to_bitstring(field_spec.enterprise_number, 32)
        return helper.bitstring_to_bytes(bitstring)
        
class Data_Records_Set:
    def __init__(self, tiny_set_id, *field_values):
        length = 2
        for val in field_values:
            length += len(val)
        self.set_header = Set_Header(tiny_set_id, length)
        self.field_values = field_values
        
    def data_records_set_to_byte(self):
        helper = TinyIPFIX_Helper_Functions()
        bitstring = ""
        bitstring += helper.field_to_bitstring(self.set_header.tiny_set_id, 8)
        bitstring += helper.field_to_bitstring(self.set_header.length, 8)
        for val in self.field_values:
            bitstring += helper.bytes_to_bitstring(val)
        return helper.bitstring_to_bytes(bitstring)

class Message:
    def __init__(self, e1, e2, sequence_number, *records_sets):
        length = 3
        if (e1 == 1):
            length += 1
        if (e2 == 1):
            length += 1
        for rec in records_sets:
            length += rec.set_header.length
        self.message_header = Message_Header(e1, e2, sequence_number, length)
        self.records_sets = records_sets
    
    def message_to_byte(self):
        helper = TinyIPFIX_Helper_Functions()
        bitstring = ""
        bitstring += helper.field_to_bitstring(self.message_header.e1, 1)
        bitstring += helper.field_to_bitstring(self.message_header.e2, 1)
        bitstring += helper.field_to_bitstring(self.message_header.set_id_lookup, 4)
        bitstring += helper.field_to_bitstring(self.message_header.length, 10)
        if self.message_header.e2 == 1:
            bitstring += helper.field_to_bitstring(self.message_header.extended_sequence_number, 16)
        else:
            bitstring += helper.field_to_bitstring(self.message_header.sequence_number, 8)
        if self.message_header.e1 == 1:
            bitstring += helper.field_to_bitstring(self.message_header.extended_set_id, 8)
        
        for rec_set in self.records_sets:
            if rec_set.set_header.tiny_set_id == 2:
                bitstring += helper.bytes_to_bitstring(rec_set.template_records_set_to_byte())
            elif 128 <= rec_set.set_header.tiny_set_id <= 255:
                bitstring += helper.bytes_to_bitstring(rec_set.data_records_set_to_byte())
            else:
                raise Exception("Unknown value for tiny_set_id")
        return helper.bitstring_to_bytes(bitstring)
    
class Received_Message:
    def __init__(self, message):
        self.message = message
    def parse_message(self, known_templates = None):
        helper = TinyIPFIX_Helper_Functions()
        msg = helper.bytes_to_bitstring(self.message)

        msg_pos = 0
        
        e1 = int(msg[msg_pos], 2)
        msg_pos += 1
        e2 = int(msg[msg_pos], 2)
        msg_pos += 1
        set_id_lookup = int(msg[msg_pos:msg_pos+4], 2)
        msg_pos += 4
        message_total_length = int(msg[msg_pos:msg_pos+10], 2)
        msg_pos+=10
        if (e2 == 1):
            sequence_number = int(msg[msg_pos:msg_pos+16], 2) # extended setquence number
            msg_pos+=16
        else:
            sequence_number = int(msg[msg_pos:msg_pos+8], 2)
            msg_pos += 8
        if (e1 == 1):
            extended_set_id = int(msg[msg_pos:msg_pos+8], 2)
            msg_pos += 8
        
        # template message (tiny setid == 2)
        if int(msg[msg_pos:msg_pos+8], 2) == 2:
            template_records_sets = []
            
            while msg_pos < message_total_length*8:
                tiny_set_id = int(msg[msg_pos:msg_pos+8], 2)
                assert(tiny_set_id == 2)
                msg_pos += 8
                length = int(msg[msg_pos:msg_pos+8])
                msg_pos += 8
                template_id = int(msg[msg_pos:msg_pos+8], 2)
                msg_pos += 8
                field_count = int(msg[msg_pos:msg_pos+8], 2)
                msg_pos += 8
                field_specifiers = []
                for i in range(field_count):
                    enterprise_bit = int(msg[msg_pos:msg_pos+1], 2)
                    msg_pos += 1
                    information_element_identifier = int(msg[msg_pos:msg_pos+15], 2)
                    msg_pos += 15
                    field_length = int(msg[msg_pos:msg_pos+8], 2)
                    msg_pos += 8
                    if(enterprise_bit == 1):
                        enterprise_number = int(msg[msg_pos:msg_pos+32], 2)
                        msg_pos += 32
                        field_specifier = Field_Specifier(enterprise_bit, information_element_identifier, field_length, enterprise_number)
                    else:
                        field_specifier = Field_Specifier(enterprise_bit, information_element_identifier, field_length)
                    field_specifiers.append(field_specifier)
                template_records_set = Template_Records_Set(Template_Record(template_id, *field_specifiers))
                template_records_sets.append(template_records_set)
            if(msg_pos != message_total_length*8):
                print("didn't read whole template message correctly")
                return None
            message = Message(e1, e2, sequence_number, *template_records_sets)
            
                        
                    
        
        # data message (128 <= tiny setid <= 255)
        # not finished !!!!!!! ##############################################################################
        elif 128 <= int(msg[msg_pos:msg_pos+8], 2) <= 255:
            if (known_templates is None) or (known_templates == []):
                print("can't parse data message, because there is no known template for the data message") # raise Exception
                return None
            data_records_sets = []
            while msg_pos < message_total_length*8:
                tiny_set_id = int(msg[msg_pos:msg_pos+8], 2)
                msg_pos += 8
                length = int(msg[msg_pos:msg_pos+8], 2)
                msg_pos += 8
                template_found = 0
                for template in known_templates:
                    if template.template_record.template_record_header.template_id == tiny_set_id:
                        template_found = 1
                        data_values = []
                        field_specifier_number = 0
                        for field_specifier in template.template_record.field_specifiers:
                            data_length = field_specifier.field_length
                            data_value = msg[msg_pos:msg_pos+(data_length*8)]
                            msg_pos += (data_length*8)
                            data_values.append(helper.bitstring_to_bytes(data_value))
                            field_specifier_number += 1
                        break
                if template_found == 0:
                    print("cannot parse data message, because there is no known template for the data message") # raise Exception
                    return None
                data_records_set = Data_Records_Set(tiny_set_id, *data_values)
                data_records_sets.append(data_records_set)
            if(msg_pos != message_total_length*8):
                print("didn't read whole data message correctly")
                return None
            message = Message(e1, e2, sequence_number, *data_records_sets)
            
                
        else:
            raise Exception("Tiny Set Id not known")
        
        
        
        
        return message