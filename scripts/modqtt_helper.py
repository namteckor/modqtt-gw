import os, sys, socket, datetime, time, math, csv, json, signal
from unittest.case import DIFF_OMITTED
from umodbus.client import tcp
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from data_helper import DataHelper

import paho.mqtt.client as paho
import paho.mqtt.publish as publish
from paho import mqtt
from dotenv import load_dotenv

import pdb

dotenv_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(dotenv_path=dotenv_path)

class ModbusHelper(object):

	FUNCTION_CODES = {
		'01': ['1','01','FC01','coil','Coil','coils','Coils','RC','Coil-FC01'],			# function code 01: Read Coils
		'02': ['2','02','FC02','discrete','Discrete','di','DI','RDI','DI-FC02'], 		# function code 02: Read Discrete Inputs
		'03': ['3','03','FC03','holding','Holding','HR','RHR','HR-FC03'], 				# function code 03: Read Holding Registers
		'04': ['4','04','FC04','input register','input registers','Input Register',
				'Input Registers','IR','RIR','IR-FC04']									# function code 04: Read Input Registers
	}

	UMODBUS_TCP_CALL = {
		'01': tcp.read_coils,
		'02': tcp.read_discrete_inputs,
		'03': tcp.read_holding_registers,
		'04': tcp.read_input_registers
	}

	DATA_TYPES_REGISTER_COUNT = {
		'uint16': 1,
		'sint16': 1,
		'float32': 2,
		'float64': 4,
		'packedbool': 1,
		'ruint16': 1,
		'rsint16': 1,
		'rfloat32_byte_swap': 2, # [A B C D] -> [B A] [D C]
		'rfloat32_word_swap': 2, # [A B C D] -> [C D] [A B]
		'rfloat32_byte_word_swap': 2, # [A B C D] -> [D C] [B A]
		#'rfloat64': 4, # unsupported at the moment, to be added; "reverse" float64 for Little-Endian interpretation
		'di': 1,
		'coil': 1
	}

	# Method to parse a modqtt template .csv configuration file and build the various Modbus TCP calls the client shall send in an "optimized" way (optimized to reduce/minimize the number of calls)
	# it returns 3 elements: call_groups, interpreter_helper, and mqtt_helper
	@classmethod
	def parse_template_build_calls(cls, full_path_to_modbus_template_csv):
		call_groups = {}
		interpreter_helper = {}
		mqtt_helper = {}
		template_lod = DataHelper.csv_to_lod(full_path_to_modbus_template_csv)
		
		# find unique/distinct read_type
		for read_entry in template_lod:
			read_address = read_entry['address']

			# skip entry if there is no address (mandatory field)
			if (not read_address) or (read_address == '') or (read_address is None):
				print('\n\t[WARNING] On item:',read_entry)
				print('\t[WARNING] Skipping item due to no address provided')
				continue

			read_type = str(read_entry['read_type'])
			read_tag_name = read_entry['tag_name']

			# skip entry if there is no read_type (mandatory field)
			if (not read_type) or (read_type == '') or (read_type is None):
				print('\n\t[WARNING] On item:',read_entry)
				print('\t[WARNING] Skipping item with address '+str(read_address)+' and tag_name "'+str(read_tag_name)+'"" due to no read_type provided\n')
				continue			
			
			# default to data_type of sint16 if user forgot to specify one
			# arbitrary choice to accomodate errors in the modbus_template...
			# logged data may be inaccurate if the real data_type is different from sint16
			read_data_type = read_entry['data_type']
			if (not read_data_type) or (read_data_type == '') or (read_data_type is None):
				print('\n\t[WARNING] No data_type specified in modbus_template for item:')
				print('\t\t',read_entry)
				print('\tAssuming default data_type of "sint16"')
				print('\t[WARNING] Logged data may be inaccurate for this item!')
				read_data_type = 'sint16'
			# skip entry if read_data_type is unknown or not currently supported
			if read_data_type not in ModbusHelper.DATA_TYPES_REGISTER_COUNT:
				print('\n\t[WARNING] On item:',read_entry)
				print('\t[WARNING] Skipping item with address '+str(read_address)+' and tag_name "'+str(read_tag_name)+'"" due to unknown or unsupported read_type of "'+str(read_data_type)+'"')
				print('\t[WARNING] Supported read_types are:',[str(i) for i in ModbusHelper.DATA_TYPES_REGISTER_COUNT])
				continue

			# create a default tag name if the user forgot to specify one
			if (not read_tag_name) or (read_tag_name == '') or (read_tag_name is None):
				print('\n\t[WARNING] No tag_name specified in modbus_template for item:')
				print('\t\t',read_entry)
				print('\tUsing default tag_name of: "'+read_type+'_address_'+str(read_address)+'_data_type_'+read_data_type+'"')
				read_tag_name = read_type+'_address_'+str(read_address)+'_data_type_'+read_data_type

			if read_tag_name not in mqtt_helper:
				mqtt_helper[read_tag_name] = {}			

			mqtt_topic = read_entry['mqtt_topic']
			mqtt_payload = read_entry['mqtt_payload']
			mqtt_qos = read_entry['mqtt_qos']
			mqtt_retain = read_entry['mqtt_retain']
			mqtt_publish = read_entry['mqtt_publish']
			mqtt_deadband = read_entry['mqtt_deadband']
			mqtt_low = read_entry['mqtt_low']
			mqtt_high = read_entry['mqtt_high']

			# set the MQTT topic, if no topic provided, the tag_name will be used as topic, otherwise the tag_name is appended to the provided topic name
			if (not mqtt_topic) or (mqtt_topic == '') or (mqtt_topic is None):
				mqtt_topic = read_tag_name
			else:
				mqtt_topic = mqtt_topic + '/' + read_tag_name
			# special case to handle packedbook data_type, create multiple topics accordingly
			if read_data_type == 'packedbool':
				mqtt_helper[read_tag_name+'_uint16_value'] = {
					'mqtt_topic': mqtt_topic+'_uint16_value'
				}
				for i in range(0,16):
					mqtt_helper[read_tag_name+'_bit'+str(i)] = {
						'mqtt_topic': mqtt_topic+'_bit'+str(i)
					}

			# set the MQTT payload, default to text if none specified or unsupported
			if (not mqtt_payload) or (mqtt_payload == '') or (mqtt_payload is None) or (mqtt_payload in ['plaintext','Plaintext','PLAINTEXT','text','Text','TEXT']):
				mqtt_payload = 'text'
			elif mqtt_payload in ['json','Json','JSON']:
				mqtt_payload = 'json'
			else:
				print('\n\t[WARNING] Unsupported mqtt_payload for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_payload of: "json"')
				mqtt_payload = 'text'	

			# set the MQTT QoS, default to 0 if none specified or unsupported
			if (not mqtt_qos) or (mqtt_qos == '') or (mqtt_qos is None):
				mqtt_qos = 0
			elif mqtt_qos in [0,1,2,'0','1','2']:
				mqtt_qos = int(mqtt_qos)
			else:
				print('\n\t[WARNING] Unsupported mqtt_qos for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_qos of: 0')
				mqtt_qos = 0

			# set the MQTT retain, default to True if none specified or unsupported
			if (not mqtt_retain) or (mqtt_retain == '') or (mqtt_retain is None):
				mqtt_retain = True
			elif mqtt_retain in [True,False]:
				mqtt_retain = mqtt_retain
			elif mqtt_retain in ['TRUE','true','True']:
				mqtt_retain = True
			elif mqtt_retain in ['FALSE','false','False']:
				mqtt_retain = False
			else:
				print('\n\t[WARNING] Unsupported mqtt_retain for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_retain of: True')
				mqtt_retain = True

			# set the MQTT publish, default to rbe if none specified or unsupported
			if (not mqtt_publish) or (mqtt_publish == '') or (mqtt_publish is None):
				mqtt_publish = 'rbe'
			elif mqtt_publish in ['rbe','RBE','Rbe','exception','report by exception','report-by-exception','Report-by-exception','Report by exception']:
				mqtt_publish = 'rbe'
			elif (isinstance(mqtt_publish,int) or isinstance(mqtt_publish,float) or isinstance(mqtt_publish,str)):
				try:
					mqtt_publish = float(mqtt_publish)
				except:
					print('\n\t[WARNING] Unsupported mqtt_publish for item:')
					print('\t\t',read_entry)
					print('\tUsing default mqtt_publish of: rbe (report by exception)')
					mqtt_publish = 'rbe'
			else:
				print('\n\t[WARNING] Unsupported mqtt_publish for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_publish of: rbe (report by exception)')
				mqtt_publish = 'rbe'

			# set the MQTT deadband, default to 0 if none specified or unsupported, if data_type is 'di' or 'coil', also if mqqt_publish is not rbe
			# note on deadband: the comparison is STRICTLY greater than, meaning if the change is exactly equal to the deadband, the value is not reported
			if (not mqtt_deadband) or (mqtt_deadband == '') or (mqtt_deadband is None):
				mqtt_deadband = float(0)
			elif read_data_type in ['di','coil']:
				mqtt_deadband = float(0)
			elif (isinstance(mqtt_publish,int) or isinstance(mqtt_publish,float)):
				mqtt_deadband = float(0)
			elif (isinstance(mqtt_deadband,int) or isinstance(mqtt_deadband,float) or isinstance(mqtt_deadband,str)):
				try:
					mqtt_deadband = float(mqtt_deadband)			
				except:
					print('\n\t[WARNING] Unsupported mqtt_deadband for item:')
					print('\t\t',read_entry)
					print('\tUsing default mqtt_deadband of: 0')
					mqtt_deadband = float(0)
			else:
				print('\n\t[WARNING] Unsupported mqtt_deadband for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_deadband of: 0')
				mqtt_deadband = float(0)

			# set the MQTT low limit if provided, if the value is equal to or lower than the low limit, it will be reported so long as this remains true, regardless of deadband changes
			if (not mqtt_low) or (mqtt_low == '') or (mqtt_low is None):
				mqtt_low = None
			elif (isinstance(mqtt_low,int) or isinstance(mqtt_low,float) or isinstance(mqtt_low,str)):
				try:
					mqtt_low = float(mqtt_low)			
				except:
					print('\n\t[WARNING] Unsupported mqtt_low for item:')
					print('\t\t',read_entry)
					print('\tUsing default mqtt_low of: None')
					mqtt_low = None
			else:
				print('\n\t[WARNING] Unsupported mqtt_low for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_low of: None')
				mqtt_low = None

			# set the MQTT high limit if provided, if the value is equal to or greater than the high limit, it will be reported so long as this remains true, regardless of deadband changes
			if (not mqtt_high) or (mqtt_high == '') or (mqtt_high is None):
				mqtt_high = None
			elif (isinstance(mqtt_high,int) or isinstance(mqtt_high,float) or isinstance(mqtt_high,str)):
				try:
					mqtt_high = float(mqtt_high)			
				except:
					print('\n\t[WARNING] Unsupported mqtt_high for item:')
					print('\t\t',read_entry)
					print('\tUsing default mqtt_high of: None')
					mqtt_high = None
			else:
				print('\n\t[WARNING] Unsupported mqtt_high for item:')
				print('\t\t',read_entry)
				print('\tUsing default mqtt_high of: None')
				mqtt_high = None
						
			# lookup the read_type in ModbusHelper.FUNCTIONS_CODES and build the lookup table
			fc_lookup_table = {}			

			fc_found = False
			for fc in ModbusHelper.FUNCTION_CODES:
				if fc_found:
					break
				for fc_keyword in ModbusHelper.FUNCTION_CODES[fc]:
					if fc_keyword in read_type:
						fc_found = True
						if read_type not in fc_lookup_table:
							fc_lookup_table[read_type] = fc
						if fc not in call_groups:
							call_groups[fc] = []
							#interpreter_helper[fc] = {'addresses': [],'address_count_map': {},'address_data_type_map':{},'address_tag_name_map': {}}
							interpreter_helper[fc] = {'addresses': [],'address_maps': {}}

						interpreter_helper[fc]['address_maps'][int(read_address)] = {}
						interpreter_helper[fc]['address_maps'][int(read_address)]['count'] = ModbusHelper.DATA_TYPES_REGISTER_COUNT[read_data_type]
						interpreter_helper[fc]['address_maps'][int(read_address)]['data_type'] = read_data_type
						interpreter_helper[fc]['address_maps'][int(read_address)]['tag_name'] = read_tag_name
						interpreter_helper[fc]['address_maps'][int(read_address)]['scaling_coeff'] = read_entry['scaling_coeff']
						interpreter_helper[fc]['address_maps'][int(read_address)]['scaling_offset'] = read_entry['scaling_offset']
						
						mqtt_helper[read_tag_name]['mqtt_topic'] = mqtt_topic
						mqtt_helper[read_tag_name]['mqtt_payload'] = mqtt_payload
						mqtt_helper[read_tag_name]['mqtt_qos'] = mqtt_qos
						mqtt_helper[read_tag_name]['mqtt_retain'] = mqtt_retain
						mqtt_helper[read_tag_name]['mqtt_publish'] = mqtt_publish
						mqtt_helper[read_tag_name]['mqtt_deadband'] = mqtt_deadband
						mqtt_helper[read_tag_name]['mqtt_low'] = mqtt_low
						mqtt_helper[read_tag_name]['mqtt_high'] = mqtt_high

						if read_data_type == 'packedbool':
							packedbool_tag_name = read_tag_name+'_uint16_value'
							mqtt_helper[packedbool_tag_name]['mqtt_payload'] = mqtt_payload
							mqtt_helper[packedbool_tag_name]['mqtt_qos'] = mqtt_qos
							mqtt_helper[packedbool_tag_name]['mqtt_retain'] = mqtt_retain
							mqtt_helper[packedbool_tag_name]['mqtt_publish'] = mqtt_publish
							mqtt_helper[packedbool_tag_name]['mqtt_deadband'] = mqtt_deadband
							mqtt_helper[packedbool_tag_name]['mqtt_low'] = mqtt_low
							mqtt_helper[packedbool_tag_name]['mqtt_high'] = mqtt_high
							
							for i in range(0,16):
								packedbool_tag_name = read_tag_name+'_bit'+str(i)
								mqtt_helper[packedbool_tag_name]['mqtt_payload'] = mqtt_payload
								mqtt_helper[packedbool_tag_name]['mqtt_qos'] = mqtt_qos
								mqtt_helper[packedbool_tag_name]['mqtt_retain'] = mqtt_retain
								mqtt_helper[packedbool_tag_name]['mqtt_publish'] = mqtt_publish
								mqtt_helper[packedbool_tag_name]['mqtt_deadband'] = mqtt_deadband
								mqtt_helper[packedbool_tag_name]['mqtt_low'] = mqtt_low
								mqtt_helper[packedbool_tag_name]['mqtt_high'] = mqtt_high

						for call_address in range(int(read_address),int(read_address)+ModbusHelper.DATA_TYPES_REGISTER_COUNT[read_data_type]):
							interpreter_helper[fc]['addresses'].append(call_address)
						break
		
		for fc in interpreter_helper:
			previous_address = None
			for address in sorted(interpreter_helper[fc]['addresses']):
				if previous_address is None:
					call_groups[fc].append({'start_address': address, 'register_count': 1})
				else:
					address_delta = address - previous_address
					if address_delta == 1:
						call_groups[fc][-1]['register_count'] += 1						
					else:
						call_groups[fc].append({'start_address': address, 'register_count': 1})
				previous_address = address

		return call_groups, interpreter_helper, mqtt_helper

	@classmethod
	def parse_json_config(cls, full_path_to_modqtt_config_json):
		with open(full_path_to_modqtt_config_json) as json_file:
			config = json.load(json_file)
		json_file.close()
		
		# perform input validation
		for key in config:
			key_value = config[key]

			# for keys/values that should be entered as string
			if key in ['modbus_server_ip','mqtt_client_id']:
				if not isinstance(key_value,str):
					print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
					print('\t[ERROR] value of key "'+str(key)+'" should be of type "string" (str)')
					print('\t[ERROR] current type of value for key "'+str(key)+'" is',type(key_value),'and current value is config["'+str(key)+'"] =',str(key_value))
					return
				# check for valid IP address format and content
				if key == 'modbus_server_ip':					
					if key_value in ['localhost','Localhost','LocalHost','LOCALHOST','Local Host','LOCAL HOST','local host']:
						config[key] = 'localhost'
						continue
					else:
						key_value_split = key_value.split('.')
						if not (len(key_value_split) == 4):
							print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
							print('\t[ERROR] incorrect IPv4 address format provided:',str(key_value))
							print('\t[ERROR] please provide a valid IPv4 address format A.B.C.D with A, B, C, and D in range [0,255]')
							return
						else:
							for octet in key_value_split:
								if not octet.isnumeric():
									print(octet,type(octet))
									print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
									print('\t[ERROR] incorrect IPv4 address format provided:',str(key_value))
									print('\t[ERROR] octet "'+str(octet)+'" is not convertible to type int')
									print('\t[ERROR] please provide a valid IPv4 address format A.B.C.D with A, B, C, and D in range [0,255]')
									return
								elif (int(octet) < 0) or (int(octet) > 255):
									print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
									print('\t[ERROR] incorrect IPv4 address provided:',str(key_value))
									print('\t[ERROR] octet "'+str(octet)+'" shall be in range [0,255]')
									print('\t[ERROR] please provide a valid IPv4 address format A.B.C.D with A, B, C, and D in range [0,255]')
									return

			# for keys/values that should be entered as integer
			elif key in ['modbus_server_port','modbus_server_id','mqtt_broker_port']:
				if not isinstance(key_value,int):
					print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
					print('\t[ERROR] value of key "'+str(key)+'" should be of type "integer" (int)')
					print('\t[ERROR] current type of value for key "'+str(key)+'" is',type(key_value),'and current value is config["'+str(key)+'"] =',str(key_value))
					return
				# check for valid TCP port range
				if (key == 'modbus_server_port') or (key == 'mqtt_broker_port'):
					if not (key_value in range(1,65536)):
						print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
						print('\t[ERROR] invalid TCP port "'+str(key_value)+'" out of valid range [1,65535] for TCP ports')
						return
					elif key_value not in [502,503,8883]:
						print('\t[WARNING] "modbus_server_port" or "mqtt_broker_port" from config file not in common Modbus TCP or MQTT ports list [502,503, 8883]:',str(key_value),'\n')
						continue
				# check for valid Modbus Server ID
				elif key == 'modbus_server_id':
					if not (key_value in range(0,256)):
						print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
						print('\t[ERROR] invalid server ID "'+str(key_value)+'" out of valid range [0,255]')
						return				
			
			# for keys/values that should be entered as either integer or float
			elif key in ['modbus_poll_interval_seconds','modbus_server_timeout_seconds']:
				if not (isinstance(key_value,int) or isinstance(config[key],float)):
					print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
					print('\t[ERROR] value of key "'+str(key)+'" should be of type "integer" (int) or "float" (float)')
					print('\t[ERROR] current type of value for key "'+str(key)+'" is',type(key_value),'and current value is config["'+str(key)+'"] =',str(key_value))
					return
			# for keys/values that should be entered as boolean, either true or false
			elif key in ['']:
				if not isinstance(key_value,bool):
					print('\t[ERROR] Error parsing config file:',str(full_path_to_modqtt_config_json))
					print('\t[ERROR] value of key "'+str(key)+'" should be of type boolen, either true or false in the .json config')
					print('\t[ERROR] current type of value for key "'+str(key)+'" is',type(key_value),'and current value is config["'+str(key)+'"] =',str(key_value))
					return

		return config

class ModbusTCPClient:
	def __init__(self, server_ip=None, server_port=None, server_id=None, poll_interval_seconds=None):
		if server_ip is None:
			print('\t[ERROR] no server_ip argument provided to ModbusTCPClient instance')
			print('\t[ERROR] server_port, server_id and poll_interval_seconds arguments will default to 502, 1, and 1 second respectively if not specified')
			print('\t[ERROR] at a minimum, the ModbusTCPClient should know which IP address to connect to')
			print('\t[ERROR] here are some examples:')
			print('\t[ERROR]\t\tmy_tcp_client = ModbusTCPClient("10.1.10.30")\t# connect to Modbus TCP Server @ 10.1.10.30 on default port 502 and with default ID 1')
			print('\t[ERROR]\t\tmy_tcp_client = ModbusTCPClient(server_ip="10.1.10.31", server_port=503, server_id=10, poll_interval_seconds=5)\t# connect to Modbus TCP Server @ 10.1.10.31 on port 503, with ID 10 and poll every 5 seconds')
			return
		else:
			self.modbus_tcp_server_ip_address = server_ip
		default_server_port = ''
		if server_port is None:
			default_server_port = '(default)'
			server_port = 502
		self.modbus_tcp_server_port = server_port
		default_server_id = ''
		if server_id is None:
			default_server_id = '(default)'
			server_id = 1
		self.modbus_tcp_server_id = server_id
		default_poll_interval = ''
		if poll_interval_seconds is None:
			default_poll_interval = '(default)'
			poll_interval_seconds = 1
		self.poll_interval_seconds = poll_interval_seconds
		self.call_groups = None
		self.interpreter_helper = None
		self.sock = None
		print('\t[INFO] Client will attempt to connect to Modbus TCP Server at:\t\t\t',str(self.modbus_tcp_server_ip_address))
		print('\t[INFO] Client will attempt to connect to Modbus TCP Server on port:\t\t',str(self.modbus_tcp_server_port),default_server_port)
		print('\t[INFO] Client will attempt to connect to Modbus TCP Server with Modbus ID:\t',str(self.modbus_tcp_server_id),default_server_id)
		print('\t[INFO] Client will attempt to poll the Modbus TCP Server every:\t\t\t',str(self.poll_interval_seconds)+' seconds',default_poll_interval)

	def load_template(self, full_path_to_modbus_template_csv=None):
		if full_path_to_modbus_template_csv is None:
			print('\t[ERROR] in ModbusTCPClient.load_template(): please make sure to provide a valid path to a modbus_template.csv file')
			return
		elif not os.path.isfile(full_path_to_modbus_template_csv):
			print('\t[ERROR] in ModbusTCPClient.load_template(): unable to find "'+str(full_path_to_modbus_template_csv)+'"')
			return
		else:
			self.call_groups, self.interpreter_helper, self.mqtt_helper = ModbusHelper.parse_template_build_calls(full_path_to_modbus_template_csv)

	def connect(self, timeout=5):
		socket.setdefaulttimeout(timeout)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		
		self.sock.connect((self.modbus_tcp_server_ip_address, self.modbus_tcp_server_port))

	def disconnect(self):
		self.sock.close()

	def interpret_response(self, response, fc, start_address):
		interpreted_response = {}
		skip_next = False
		skip_count = 0
		for i in range(len(response)):
			address_index = i + start_address
			if fc in ['01', '02']:
				#interpreted_response[self.interpreter_helper[fc]['address_tag_name_map'][address_index]] = response[i]
				interpreted_response[self.interpreter_helper[fc]['address_maps'][address_index]['tag_name']] = response[i]
			else:
				if skip_next:
					if skip_count == 0:
						skip_next = False
					elif skip_count == 1:
						skip_count -= 1
						skip_next = False
					else:
						skip_count -= 1
					continue								

				#given_data_type = self.interpreter_helper[fc]['address_data_type_map'][address_index]
				given_data_type = self.interpreter_helper[fc]['address_maps'][address_index]['data_type']
				if given_data_type == 'float32':
					float_32_items = response[i:i+2]
					float_32_binaries = [DataHelper.int_16_unsigned_to_binary(reg) for reg in float_32_items]
					rv = DataHelper.binary_32_to_ieee_754_single_precision_float(''.join(float_32_binaries))
					skip_next = True
				elif given_data_type == 'sint16':
					rv = DataHelper.int_16_unsigned_to_signed(response[i])
					skip_next = False
				elif given_data_type == 'uint16':
					rv = response[i]
					skip_next = False
				elif given_data_type == 'float64':
					float_64_items = response[i:i+4]
					float_64_binaries = [DataHelper.int_16_unsigned_to_binary(reg) for reg in float_64_items]
					rv = DataHelper.binary_64_to_ieee_754_single_precision_float(''.join(float_64_binaries))
					skip_next = True
					skip_count = 3
				elif given_data_type == 'rsint16':
					swapped_rv = DataHelper.binary_string_16_bits_to_int_16_unsigned(DataHelper.int_16_swap_bytes(DataHelper.int_16_unsigned_to_binary(response[i])))
					rv = DataHelper.int_16_unsigned_to_signed(swapped_rv)
					skip_next = False
				elif given_data_type == 'ruint16':
					rv = DataHelper.binary_string_16_bits_to_int_16_unsigned(DataHelper.int_16_swap_bytes(DataHelper.int_16_unsigned_to_binary(response[i])))					
					skip_next = False
				elif given_data_type == 'packedbool':
					binary_string_register = DataHelper.int_16_unsigned_to_binary(response[i])
					binary_string_register_list = []
					binary_string_register_list[:0]= binary_string_register 
					skip_next = False
				elif given_data_type == 'rfloat32_byte_swap':
					float_32_items = response[i:i+2]
					float_32_binary_string = ''.join([DataHelper.int_16_unsigned_to_binary(reg) for reg in float_32_items])
					swapped_rv = DataHelper.float32_swap_bytes(float_32_binary_string)
					rv = DataHelper.binary_32_to_ieee_754_single_precision_float(swapped_rv)
					skip_next = True
				elif given_data_type == 'rfloat32_word_swap':
					float_32_items = response[i:i+2]
					float_32_binary_string = ''.join([DataHelper.int_16_unsigned_to_binary(reg) for reg in float_32_items])
					swapped_rv = DataHelper.float32_swap_words(float_32_binary_string)
					rv = DataHelper.binary_32_to_ieee_754_single_precision_float(swapped_rv)
					skip_next = True
				elif given_data_type == 'rfloat32_byte_word_swap':
					float_32_items = response[i:i+2]
					float_32_binary_string = ''.join([DataHelper.int_16_unsigned_to_binary(reg) for reg in float_32_items])
					swapped_rv = DataHelper.float32_swap_bytes_words(float_32_binary_string)
					rv = DataHelper.binary_32_to_ieee_754_single_precision_float(swapped_rv)
					skip_next = True
				else:
					print('\t[ERROR] unsupported data_type of "'+str(given_data_type)+'" on tag_name = "'+self.interpreter_helper[fc]['address_maps'][address_index]['tag_name']+'"')
					skip_next = False
					continue

				# evaluate scaling to apply
				applied_coeff = self.interpreter_helper[fc]['address_maps'][address_index]['scaling_coeff']
				applied_offset = self.interpreter_helper[fc]['address_maps'][address_index]['scaling_offset']
				if (not applied_coeff) ^ (not applied_offset):
					one_scaling_null = True
					applied_coeff_null = not applied_coeff
					both_null_case = False
				elif (not applied_coeff) & (not applied_offset):
					both_null_case = True
				else:
					applied_coeff_null = (math.isnan(float(applied_coeff)) or (applied_coeff is None))
					one_scaling_null =  applied_coeff_null ^ (math.isnan(float(applied_offset)) or (applied_offset is None))
					both_null_case = (math.isnan(float(applied_coeff)) or (applied_coeff is None)) & (math.isnan(float(applied_offset)) or (applied_offset is None))
				if not both_null_case:
					if not (given_data_type == 'packedbool'):
						if one_scaling_null:
							if applied_coeff_null:
								applied_coeff = 1
							else:
								applied_offset = 0
						rv = rv*float(applied_coeff) + float(applied_offset)

				if given_data_type == 'packedbool':					
					interpreted_response[self.interpreter_helper[fc]['address_maps'][address_index]['tag_name']+'_uint16_value'] = response[i]
					for string_char_pos, string_char in enumerate(binary_string_register_list):
						suffix = str(15 - string_char_pos)
						interpreted_response[self.interpreter_helper[fc]['address_maps'][address_index]['tag_name']+'_bit'+suffix] = int(string_char)
				else:
					interpreted_response[self.interpreter_helper[fc]['address_maps'][address_index]['tag_name']] = rv

		return interpreted_response
	
	def combine_tag_responses(self, lod):
		combined_responses = {}
		for resp in lod:
			for tag in resp:
				combined_responses[tag] = resp[tag]
		return combined_responses

	def cycle_poll(self, time_format = '%Y-%m-%d %H:%M:%S%z'):
		ts_local = datetime.datetime.now().astimezone()
		ts_utc = ts_local.astimezone(datetime.timezone.utc)
		all_interpreted_responses = [{'timestamp_utc': ts_utc.strftime(time_format), 'timestamp_local': ts_local.strftime(time_format)}]
		for modbus_call in self.call_groups:
			modbus_request = ModbusHelper.UMODBUS_TCP_CALL[modbus_call]
			for query in self.call_groups[modbus_call]:
				message = modbus_request(slave_id=self.modbus_tcp_server_id, starting_address=query['start_address'], quantity=query['register_count'])

				# Response depends on Modbus function code.
				response = tcp.send_message(message, self.sock)
				interpreted_response = self.interpret_response(response, modbus_call, query['start_address'])
				all_interpreted_responses.append(interpreted_response)
		combined_responses = self.combine_tag_responses(all_interpreted_responses)
		return combined_responses

	def pretty_print_interpreted_response(self, to_print, max_items_per_line=5):
		headers = list(to_print.keys())		
		header_max_length = max([len(str(h)) for h in headers])
		values = list(to_print.values())
		value_max_length = max([len(str(v)) for v in values])
		max_length = max(header_max_length,value_max_length)

		headers_padded = [h.ljust(max_length) for h in headers]
		values_padded = [str(v).ljust(max_length) for v in values]
		
		print('')
		for i in range(0,len(headers_padded),max_items_per_line):			
			header_line = ' | '.join(str(x) for x in headers_padded[i:i+max_items_per_line])
			value_line = ' | '.join(str(v) for v in values_padded[i:i+max_items_per_line])
			sep_line = '-'.ljust(len(header_line),'-')
			print('\t',sep_line)
			print('\t',header_line)
			print('\t',value_line)
		print('\t',sep_line)
		print('')

class ModbusTCPMqttDataGateway:
	def termination_signal_handler(self, signal, frame):
		print('\nYou pressed Ctrl+C!')
		self.modbus_tcp_client.disconnect()		
		self.mqttc.loop_stop()
		self.mqttc.disconnect()
		print('Bye!')
		time.sleep(2)
		sys.exit(0)	
	
	# setting callbacks for on_connect events, print some debug feedback
	def on_connect(self, client, userdata, flags, rc, properties=None):
		print('\t[INFO] **MQTT** CONNACK received with code %s.' % rc)
		if rc == 0:
			print('\t[INFO] **MQTT** Connected to MQTT Broker!')
			self.mqtt_connected = True
		else:
			print('\t[INFO] **MQTT** Failed to connect, return code %d\n', rc)

	# setting callback for on_publish event, check if publish was successful
	def on_publish(self, client, userdata, mid, properties=None):
		print('\t[INFO] **MQTT**',json.dumps(
				{
					'client': str(client),
					'userdata': str(userdata),
					'mid': str(mid),
				}
			)		
		)
		self.mqtt_last_successful_mid_count += 1

	# handle disconnects
	def on_disconnect(self, client, userdata, rc):
		print('\t[INFO] **MQTT** Client got disconnected...')

	# used this for testing only, slow and inefficient as it tears down the connection to broker at every publish...
	def mqtt_publish_multiple(self,lod):
		publish.multiple(
				msgs=lod, 
				hostname=self.mqtt_broker_url, 
				port=self.modqtt_config['mqtt_broker_port'], 
				client_id=self.modqtt_config['mqtt_client_id'], 
				keepalive=60, 
				will=None, 
				auth= {'username':self.mqtt_broker_creds_username, 'password':self.mqtt_broker_creds_password}, 
				tls= {'tls_version':mqtt.client.ssl.PROTOCOL_TLS}, #{'ca_certs':"", 'certfile':"", 'keyfile':"", 'tls_version':mqtt.client.ssl.PROTOCOL_TLS, 'ciphers':""}, 
				protocol=paho.MQTTv5, 
				transport="tcp"
			)
	
	def mqtt_parse_publish_tag(self, tag_key, tag_current_value, ts_utc, ts_local,limit_flag=False):
		tag_topic = self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_topic']
		tag_qos = self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_qos']
		tag_retain = self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_retain']
		tag_payload = self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_payload']
		if tag_payload == 'json':
			tag_value = {
				'timestamp_utc': ts_utc,
				'timestamp_local': ts_local,
				'value': tag_current_value
			}
			tag_value = json.dumps(tag_value)
		elif tag_payload == 'text':
			tag_value = str(tag_current_value)										
		
		self.mqqt_last_published_values[tag_key]={
			'timestamp_utc':ts_utc,
			'timestamp_local':ts_local,
			'last_published_value': tag_current_value,
			'limit_flag': limit_flag
		}		
		self.mqtt_client_publish_count += 1
		publish_result = self.mqttc.publish(tag_topic, payload=tag_value, qos=tag_qos, retain=tag_retain)											
		print('\t[INFO] **MQTT**',publish_result)
		publish_status = publish_result[0]
		if publish_status == 0:
			print('\t[INFO] **MQTT** Sent: '+str(tag_value)+' to topic "'+str(tag_topic)+'" with qos='+str(tag_qos)+' and retain='+str(tag_retain))
		else:
			print('\t[INFO] **MQTT** Failed to send message to topic "'+str(tag_topic)+'"')
	
	def mqtt_publish_data(self, previous_values, current_values, mqtt_client=None,time_format = '%Y-%m-%d %H:%M:%S%z'):
		if mqtt_client is None:
			mqtt_client = self.mqttc			 	
		
		# every time the modqtt gateway instance is freshly started, it will connect and publish all the data tags
		if previous_values is None:
			for tag_key in current_values:
				if tag_key == 'timestamp_utc':
					ts_utc = current_values[tag_key]
					continue
				elif tag_key == 'timestamp_local':
					ts_local = current_values[tag_key]
					continue
				else:
					tag_current_value = current_values[tag_key]
					self.mqtt_parse_publish_tag(
							tag_key = tag_key,
							tag_current_value = tag_current_value,
							ts_utc = ts_utc,
							ts_local = ts_local
						)					

			while (self.mqtt_client_publish_count > self.mqtt_last_successful_mid_count):
				waiting = 1

		# logic to only publish what is relevant (i.e. deadband changes, high/low limits reached/recovered, etc.)
		else:
			for tag_key in current_values:
				if tag_key == 'timestamp_utc':
					ts_utc = current_values[tag_key]
					# previous_ts_utc = previous_values[tag_key]					
					continue
				elif tag_key == 'timestamp_local':
					ts_local = current_values[tag_key]
					# previous_ts_local = previous_values[tag_key]
					continue
				else:
					ts_utc_previously_published = self.mqqt_last_published_values[tag_key]['timestamp_utc']
					tag_time_elapsed = datetime.datetime.strptime(ts_utc,time_format) - datetime.datetime.strptime(ts_utc_previously_published,time_format)
					tag_current_value = current_values[tag_key]
					# tag_previous_value = previous_values[tag_key]
					tag_previously_published_value = self.mqqt_last_published_values[tag_key]['last_published_value']
					# tag_delta_value = abs((float(tag_current_value) - float(tag_previous_value)))
					tag_delta_value_last_published = abs((float(tag_current_value) - float(tag_previously_published_value))) 
					
					tag_publish = self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_publish']
					
					# regardless of reporting/upload method, if the value falls outside of high/low limits (assuming they are not None), it is reported
					if self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_low'] is not None:
						if float(tag_current_value) <= self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_low']:
							self.mqtt_parse_publish_tag(
									tag_key = tag_key,
									tag_current_value = tag_current_value,
									ts_utc = ts_utc,
									ts_local = ts_local,
									limit_flag=True
								)
							continue
						# handle alarm recovery
						elif self.mqqt_last_published_values[tag_key]['limit_flag']:
							self.mqtt_parse_publish_tag(
									tag_key = tag_key,
									tag_current_value = tag_current_value,
									ts_utc = ts_utc,
									ts_local = ts_local,
									limit_flag=False
								)
							continue
					if self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_high'] is not None:
						if float(tag_current_value) >= self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_high']:
							self.mqtt_parse_publish_tag(
								tag_key = tag_key,
								tag_current_value = tag_current_value,
								ts_utc = ts_utc,
								ts_local = ts_local,
								limit_flag=True
							)
							continue
						# handle alarm recovery
						elif self.mqqt_last_published_values[tag_key]['limit_flag']:
							self.mqtt_parse_publish_tag(
									tag_key = tag_key,
									tag_current_value = tag_current_value,
									ts_utc = ts_utc,
									ts_local = ts_local,
									limit_flag=False
								)
							continue

					# if the tag is configured to be uploaded via 'rbe', withih high/low limits, then the deadband is considered, i.e. the current value is compared against the last reported/published value
					if tag_publish == 'rbe':
						if tag_delta_value_last_published > self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_deadband']:	#tag_delta_value > self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_deadband']:							
							self.mqtt_parse_publish_tag(
									tag_key = tag_key,
									tag_current_value = tag_current_value,
									ts_utc = ts_utc,
									ts_local = ts_local
								)
						else:
							continue
					# if the tag is configured to be uploaded at a regular interval, then the deadband is ignored, unless the -d "force deadband" switch is activated (to be added)
					elif float(tag_time_elapsed.seconds) >= float(tag_publish):
						tag_current_value = current_values[tag_key]
						
						if not self.mqtt_force_deadband:
							self.mqtt_parse_publish_tag(
								tag_key = tag_key,
								tag_current_value = tag_current_value,
								ts_utc = ts_utc,
								ts_local = ts_local
							)
						elif tag_delta_value_last_published > self.modbus_tcp_client.mqtt_helper[tag_key]['mqtt_deadband']:				
							self.mqtt_parse_publish_tag(
								tag_key = tag_key,
								tag_current_value = tag_current_value,
								ts_utc = ts_utc,
								ts_local = ts_local
							)

		print('\t[INFO] **MQTT** MQTT publish cycle complete!')
		return
	
	def __init__(self, full_path_to_modqtt_config_json=None, full_path_to_modqtt_template_csv=None, force_deadband=False, quiet=False):
		if full_path_to_modqtt_config_json is None:
			print('\t[ERROR] a modqtt config.json file is required for a ModbusTCPDataLogger instance')
			print('\t[ERROR] please provide the full path to the modqtt config.json file')
			return
		if full_path_to_modqtt_template_csv is None:
			print('\t[ERROR] a modqtt template.csv file is required for a ModbusTCPDataLogger instance')
			print('\t[ERROR] please provide the full path to the modqtt template.csv file')
			return
				
		self.modqtt_config = ModbusHelper.parse_json_config(full_path_to_modqtt_config_json)
		if self.modqtt_config is None:
			print('\t[ERROR] An error occured while parsing the modqtt json configuration file!')
			print('\t[ERROR] Please review the error messages, correct the modqtt json configuration file and try again.')
			print('\t[ERROR] Now exiting Python with sys.exit()')
			sys.exit()		

		self.mqtt_force_deadband = force_deadband
		self.mqtt_broker_url = os.environ.get('mqtt_broker_url')
		self.mqtt_broker_creds_username = os.environ.get('mqtt_broker_creds_username')
		self.mqtt_broker_creds_password = os.environ.get('mqtt_broker_creds_password')
		self.mqtt_connected = False
		self.mqtt_last_successful_mid_count = 0
		self.mqtt_client_publish_count = 0
		self.mqqt_last_published_values = {}
		# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
		# userdata is user defined data of any type, updated by user_data_set()
		# client_id is the given name of the client
		self.mqttc = paho.Client(client_id=self.modqtt_config['mqtt_client_id'], userdata=None, protocol=paho.MQTTv5)
		self.mqttc.on_connect = self.on_connect

		# enable TLS for secure connection
		if self.modqtt_config['mqtt_broker_tls']:
			self.mqttc.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
		# set username and password
		self.mqttc.username_pw_set(self.mqtt_broker_creds_username, self.mqtt_broker_creds_password)		

		self.mqttc.on_publish = self.on_publish		
		
		# connect to MQTT Broker on specified port
		self.mqttc.connect(self.mqtt_broker_url, self.modqtt_config['mqtt_broker_port'])		

		self.mqttc.loop_start()

		# Wait for connection before moving forward
		while self.mqtt_connected != True:
			time.sleep(0.1)

		self.modbus_tcp_client = ModbusTCPClient(
				server_ip=self.modqtt_config['modbus_server_ip'],
				server_port=self.modqtt_config['modbus_server_port'],
				server_id=self.modqtt_config['modbus_server_id'],
				poll_interval_seconds=self.modqtt_config['modbus_poll_interval_seconds']
			)
		self.modbus_tcp_client.load_template(full_path_to_modqtt_template_csv)
		self.modbus_tcp_client.connect(self.modqtt_config['modbus_server_timeout_seconds'])				

		signal.signal(signal.SIGINT, self.termination_signal_handler)

		print('Press Ctrl+C to stop and exit gracefully...')
		previous_response = None
		while True:
			#wake_up_time = datetime.datetime.now() + datetime.timedelta(seconds=self.modqtt_config['modbus_poll_interval_seconds'])
			modbus_poll_response = self.modbus_tcp_client.cycle_poll()						
			
			if not quiet:
				self.modbus_tcp_client.pretty_print_interpreted_response(modbus_poll_response)
				print('Press Ctrl+C to stop and exit gracefully...')
			
			self.mqtt_publish_data(
					previous_values = previous_response,
					current_values = modbus_poll_response,
					mqtt_client=self.mqttc
				)			
			
			#time.sleep(self.modqtt_config['poll_interval_seconds'])			
			wake_up_time = datetime.datetime.now() + datetime.timedelta(seconds=self.modqtt_config['modbus_poll_interval_seconds'])
			while (wake_up_time > datetime.datetime.now()):
				kill_time = 1

			previous_response = modbus_poll_response