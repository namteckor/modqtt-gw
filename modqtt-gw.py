#!/usr/bin/python3

import sys, getopt, datetime
from scripts import modbus_helper

def help_and_exit():
	print('\tUsage: path/to/modqtt-gw.py')
	print('\t\t'+'-c <path to Modbus configuration file (.json format)> (--config) [REQUIRED]')
	print('\t\t'+'-t <path to Modbus template file (.csv format)> (--template) [REQUIRED]')
	print('\t\t'+'-q <to be quiet and to not display the interval Modbus reads, default False> (--quiet) [optional]')
	print('\t\t'+'-h to show the help message and exit (--help) [optional]')
	sys.exit()

def display_error_message():
	print('\tERROR! For help please try:')
	print('\t\tpath/to/modqtt-gw.py -h')
	print('\t\tor')
	print('\t\tpython3 path/to/modqtt-gw.py -h')

time_format = '%Y-%m-%d %H:%M:%S%z'

start_local = datetime.datetime.now().astimezone()
start_utc = start_local.astimezone(datetime.timezone.utc)

argv = sys.argv[1:]

short_options = 'c:t:qh' 
long_options =  ['config=','template=','quiet','--help']

try:
	opts, args = getopt.getopt(argv,short_options,long_options)
except getopt.error as err:
	print(str(err))
	print('')
	display_error_message()
	print('')
	help_and_exit()

list_of_options_passed = []
for item in opts:
	list_of_options_passed.append(item[0])

if ('-h' not in list_of_options_passed) and ('--help' not in list_of_options_passed):
	if ('-c' not in list_of_options_passed) and ('--config' not in list_of_options_passed):
		print('\tERROR!')
		print('\tMissing required argument -c or --config <path to Modbus configuration file (.json format)> [REQUIRED]')
		print('')
		display_error_message()
		print('')
		help_and_exit()
	elif ('-t' not in list_of_options_passed) and ('--template' not in list_of_options_passed):
		print('\tERROR!')
		print('\tMissing required argument -t or --template <path to Modbus template file (.csv format)> [REQUIRED]')
		print('')
		display_error_message()
		print('')
		help_and_exit()

# Set some defaults
be_quiet = False
output_log_files_location = None
data_logging = True

for opt, arg in opts:
	if opt in ('-h', '--help'):
		print('Usage: modqtt-gw.py [-h] -c CONFIG_FILE -t TEMPLATE_FILE [-o OUTPUT_FOLDER] [-q] [-n]')
		print('')
		print('OPTIONS:')
		print('\t-h, --help\tshow this help message and exit')
		print('\t-c CONFIG_FILE, --config CONFIG_FILE')
		print('\t\t\t.json configuration file to use (defines the Modbus TCP Server to connect to and log file properties)')
		print('\t-t TEMPLATE_FILE, --template TEMPLATE_FILE')
		print('\t\t\t.csv template file to use (defines the Modbus registers to poll, mapped tag names, scaling)')		
		print('\t-q, --quiet\tmute the display of scanned data to the terminal prompt')
		sys.exit()
	elif opt in ('-c', '--config'):
		modbus_config_location = str(arg)
	elif opt in ('-t', '--template'):
		modbus_template_location = str(arg)	
	elif opt in ('-q','--quiet'):
		be_quiet = True
	else:
		print('')
		display_error_message()
		print('')
		help_and_exit()

print('')
print('\t[INFO] start_local\t=', start_local.strftime(time_format))
print('\t[INFO] start_utc\t=', start_utc.strftime(time_format))
print('')

modbus_mqtt_gateway = modbus_helper.ModbusTCPMqttDataGateway(
		full_path_to_modbus_config_json=modbus_config_location, 
		full_path_to_modbus_template_csv=modbus_template_location, 
		quiet=be_quiet
	)		