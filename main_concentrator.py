from tinyIPFIX import TinyIPFIX_Helper_Functions
from concentrator import Concentrator

#my_concentrator = Concentrator('superb', node_number = 5, data_measure_interval = 10, template_measure_interval = 60, data_sets_per_message = 2, read_interval = 2.5, template_sets_per_message = 2, set_size = 512)
my_concentrator = Concentrator('esp32', node_number = 5, data_measure_interval = 10, template_measure_interval = 60, data_sets_per_message = 2, read_interval = 2.5, template_sets_per_message = 2, set_size = 512)

my_concentrator.run()
