from tinyIPFIX import TinyIPFIX_Helper_Functions
from end_device import End_Device


#if __name__ == '__main__':
#my_device = Device('esp32', 'end_device', node_number = 3, data_measure_interval = 5, template_measure_interval = 10, data_sets_per_message = 2)
#my_device = Device('esp32', 'aggregator', node_number = 4, data_measure_interval = 5, template_measure_interval = 10, data_sets_per_message = 2, read_interval = 2.5, template_sets_per_message = 2, set_size = 1)
#my_device.run()

my_end_device = End_Device('esp32', node_number = 4, data_measure_interval = 5, template_measure_interval = 10, data_sets_per_message = 2)

my_end_device.run()