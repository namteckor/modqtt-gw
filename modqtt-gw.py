#!/usr/bin/python3

import sys, getopt, datetime
from scripts import modqtt_helper

def help_and_exit():
	print('\tUsage: path/to/modqtt-gw.py')
	print('\t\t'+'-c <path to Modbus configuration file (.json format)> (--config) [REQUIRED]')
	print('\t\t'+'-t <path to Modbus template file (.csv format)> (--template) [REQUIRED]')
	print('\t\t'+'-e <path to .env file with MQTT broker URL and username/password information> (--env) [REQUIRED]')
	print('\t\t'+'-f <to force the deadband logic on MQTT interval uploads, i.e. if set to True, do not report unless changes exceed the deadband, default False> (--force-deadband) [optional]')
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

short_options = 'c:t:e:fqh' 
long_options =  ['config=','template=','env=','force-deadband','quiet','help']

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
	elif ('-e' not in list_of_options_passed) and ('--env' not in list_of_options_passed):
		print('\tERROR!')
		print('\tMissing required argument -e or --env <path to .env file with MQTT broker URL and username/password information> [REQUIRED]')
		print('')
		display_error_message()
		print('')
		help_and_exit()

# Set some defaults
be_quiet = False
force_deadband = False

for opt, arg in opts:
	if opt in ('-h', '--help'):
		print('Usage: modqtt-gw.py [-h] -c CONFIG_FILE -t TEMPLATE_FILE -e ENV_FILE [-f] [-q]')
		print('')
		print('OPTIONS:')
		print('\t-h, --help\tshow this help message and exit')
		print('\t-c CONFIG_FILE, --config CONFIG_FILE')
		print('\t\t\t.json configuration file to use (defines the Modbus TCP Server to connect to and log file properties)')
		print('\t-t TEMPLATE_FILE, --template TEMPLATE_FILE')
		print('\t\t\t.csv template file to use (defines the Modbus registers to poll, mapped tag names, scaling)')	
		print('\t-e ENV_FILE, --env ENV_FILE')
		print('\t\t\t.env environment file to use (defines the MQTT broker URL and username/password)')	
		print('\t-f, --force-deadband\tforce the deadband logic on MQTT interval uploads')
		print('\t-q, --quiet\tmute the display of scanned data to the terminal prompt')
		sys.exit()
	elif opt in ('-c', '--config'):
		modqtt_config_location = str(arg)
	elif opt in ('-t', '--template'):
		modqtt_template_location = str(arg)	
	elif opt in ('-e','--env'):
		modqtt_env_location = str(arg)	
	elif opt in ('-f','--force-deadband'):
		force_deadband = True
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

modbus_mqtt_gateway = modqtt_helper.ModbusTCPMqttDataGateway(
		full_path_to_modqtt_config_json=modqtt_config_location, 
		full_path_to_modqtt_template_csv=modqtt_template_location, 
		full_path_to_modqtt_env=modqtt_env_location,
		force_deadband=force_deadband,
		quiet=be_quiet
	)		