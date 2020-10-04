from tinyIPFIX import TinyIPFIX_Helper_Functions
from end_device import End_Device

my_end_device = End_Device('esp32', node_number = 1, data_measure_interval = 10, template_measure_interval = 60, data_sets_per_message = 2)
#my_end_device = End_Device('superb', node_number = 1, data_measure_interval = 10, template_measure_interval = 60, data_sets_per_message = 2)

my_end_device.run()
