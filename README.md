# modqtt-gw
**modbus-gw** is a unidirectional gateway for passing and publishing Modbus TCP data to MQTT implemented in Python based on [umodbus](https://github.com/AdvancedClimateSystems/uModbus) for the Modbus TCP client side and on [paho-mqtt](https://pypi.org/project/paho-mqtt/) for the MQTT client side.  

## Notes  
* modqtt-gw is currently a functional proof of concept, suitable for small scale applications  
* My main objectives were to learn about MQTT and hide the complexity of these two protocols behind straightforward configuration/template files  
* The Modbus and MQTT elements are currently **__tightly coupled__** (i.e. if the Modbus TCP connection is interrupted the whole script stops and must be restarted). I am aware of this design limitation and plan to work on decoupling these two elements to make the script more robust and more usable.  

## Pre-requisite  
There are two (2) important configuration files to setup for modqtt-gw to work properly:  
&ensp;(1) a Modbus and MQTT **configuration file** in .json format (-c CONFIG_FILE, --config CONFIG_FILE); this is where you define the Modbus TCP Server and MQTT Broker to connect to (IP:Port:ID), the Modbus scan rate, MQTT version, MQTT TLS settings, etc.  
&ensp;(2) a Modbus and MQTT **template file** in .csv format (-t TEMPLATE_FILE, --template TEMPLATE_FILE); this is where you define which register addresses to query, their read type (ex: Holding Registers, Input Registers) and data type (ex: float32, uint16, coil), their mapping into a more user-friendly tag name, apply linear scaling if needed, and define all the MQTT upload attributes   
When calling modqtt-gw, pass the path to these two (2) configuration files as arguments. 

## Usage  
```text
$ (python3) path/to/modqtt-gw.py
    -c <path to Modbus and MQTT configuration file (.json format)> (--config) [REQUIRED]s
	-t <path to Modbus and MQTT template file (.csv format)> (--template) [REQUIRED]
	-e <path to .env file with username/password information used for authentication with the MQTT broker> (--env) [optional]
	-C <string path to the Certificate Authority (CA) certificate files that are to be treated as trusted by this client (ex: some/path/ca.crt)> (--ca-certs) [optional]
	-F <string pointing to the PEM encoded client certificate file (ex: some/path/client.crt)> (--certfile) [optional]
	-K <string pointing to the PEM encoded client private key file (ex: some/path/client.key)> (--keyfile) [optional]
	-f <to force the deadband logic on MQTT interval uploads, i.e. if set to True, do not report unless changes exceed the deadband, default False> (--force-deadband) [optional]
	-q <to be quiet and to not display the interval Modbus reads, default False> (--quiet) [optional]
	-h to show the help message and exit (--help) [optional]'
```

## Configuration & Template files  
### (1) Modbus/MQTT configuration file in .json format   
To be added soon..  

### (2) Modbus/MQTT template file in .csv format  
To be added soon..

Additional README details to be added soon...