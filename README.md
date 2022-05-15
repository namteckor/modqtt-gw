# modqtt-gw
**modqtt-gw** is a unidirectional gateway for passing and publishing Modbus TCP data to MQTT implemented in Python based on [uModbus](https://github.com/AdvancedClimateSystems/uModbus) for the Modbus TCP client side and on [paho-mqtt](https://pypi.org/project/paho-mqtt/) for the MQTT client side.  

## Notes  
* modqtt-gw is currently a functional proof of concept, suitable for small scale applications  
* My main objectives were to learn about MQTT and hide the complexity of these two protocols behind straightforward configuration/template files  
* The Modbus and MQTT elements are currently **__tightly coupled__** (i.e. if the Modbus TCP connection is interrupted the whole script stops and must be restarted). I am aware of this design limitation and plan to work on decoupling these two elements to make the script more robust and more usable.  

## Pre-requisite  
There are two (2) important configuration files to setup for modqtt-gw to work properly:  
&ensp;(1) a Modbus and MQTT **configuration file** in .json format (-c CONFIG_FILE, --config CONFIG_FILE); this is where you define the Modbus TCP Server (IP/hostname:Port:ID) and MQTT Broker to connect to (IP/URL:Port), the Modbus scan rate, MQTT version, MQTT TLS settings, MQTT authentication option, etc.  
&ensp;(2) a Modbus and MQTT **template file** in .csv format (-t TEMPLATE_FILE, --template TEMPLATE_FILE); this is where you define which Modbus register addresses to query, their read type (ex: Holding Registers, Input Registers) and data type (ex: float32, uint16, coil), their mapping into a more user-friendly tag name, apply linear scaling if needed, and define all the MQTT upload attributes   
When calling modqtt-gw, pass the path to these two (2) configuration files as arguments. 

## Usage  
```text
$ (python3) path/to/modqtt-gw.py
    -c <path to Modbus and MQTT configuration file (.json format)> (--config) [REQUIRED]
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
#### modbus_server_ip
&ensp;'modbus_server_ip': a correctly formatted string representing the IP address or hostname of the Modbus TCP Server to connect to; ex: "10.0.1.10" or "localhost"  
#### modbus_server_port
&ensp;'modbus_server_port': a strictly positive integer [1;65535] representing the TCP port where the Modbus TCP Server process is running; ex: 502  
#### modbus_server_id
&ensp;'modbus_server_id': a positive integer [0;255] representing the Modbus Server ID in use by the Modbus TCP Server; ex: 10  
#### modbus_server_timeout_seconds
&ensp;'modbus_server_timeout_seconds': a positive floating point representing the number of seconds to use as timeout when connecting to the Modbus TCP Server; ex: 3.0  
#### modbus_poll_interval_seconds
&ensp;'modbus_poll_interval_seconds': a positive floating point representing the time interval in seconds between two (2) consecutive Modbus polls (i.e. scan rate); ex: 1.0  
#### mqtt_client_id
&ensp;'mqtt_client_id': a string representing the MQTT Client ID to use, chosen by the MQTT client and used as prefix/root to all MQTT topics for this client  
#### mqtt_broker_ip_or_url
&ensp;'mqtt_broker_ip_or_url': a correctly formatted string representing the IP address, hostname or URL of the MQTT Broker to connect to; ex: "mqtt-broker-online.com" or "localhost"  
#### mqtt_broker_port
&ensp;'mqtt_broker_port': a strictly positive integer [1;65535] representing the TCP port where the MQTT Broker process is running; ex: 8883  
#### mqtt_connection_monitoring
&ensp;'mqtt_connection_monitoring': boolean, either true or false; if true, the MQTT Client will monitor its connection status with the MQTT Broker and communicate the times of last connections/disconnections to the broker on a dedicated topic "_connection_monitoring"  
#### mqtt_broker_tls
&ensp;'mqtt_broker_tls': boolean, either true or false;
#### mqtt_tls_insecure_set
&ensp;'mqtt_tls_insecure_set': boolean, either true or false; true **NOT** recommended (insecure), see [documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php): "Configure verification of the server hostname in the server certificate."  
#### mqtt_v5
&ensp;'mqtt_v5': boolean, either true or false; set to true to use MQTT v5 (highest priority)  
#### mqtt_v311
&ensp;'mqtt_v311': boolean, either true or false; set to true to use MQTT v3.1.1 (second highest priority)  
#### mqtt_v31
&ensp;'mqtt_v31': boolean, either true or false; set to true to use MQTT v3.1.0 (least priority)  
#### mqtt_max_inflight_messages_set
&ensp;'mqtt_max_inflight_messages_set': a positive integer value; see [Eclipse - paho - Python Client - documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php): "Set the maximum number of messages with QoS>0 that can be part way through their network flow at once.
Defaults to 20. Increasing this value will consume more memory but can increase throughput."

### (2) Modbus/MQTT template file in .csv format  
To be added soon..

Additional README details to be added soon...
