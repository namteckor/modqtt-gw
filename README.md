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
## Authentication
### Username/password authentication (.env file)
Format and content:
```text
mqtt_broker_creds_username=<insert-username-here>
mqtt_broker_creds_password=<insert-password-here>
```
This is where the username and password used for basic authentication with the MQTT Broker are set and stored. Pass the path to this .env file with the -e switch (--env) if needed.  
### Certificates-based authentication
See [tls_set()](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php):
* -C (--ca-certs) ~ ca_certs; "Certificate Authority certificate files that are to be treated as trusted by this client"  
* -F (--certfile) ~ certfile; "PEM encoded client certificate"   
* -K (--keyfile) ~ keyfile; "PEM encoded client private key"  
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
&ensp;'mqtt_broker_tls': boolean, either true or false; whether to use TLS (true) or not (false); see [tls_set()](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)  
#### mqtt_tls_insecure_set
&ensp;'mqtt_tls_insecure_set': boolean, either true or false; true **NOT** recommended (insecure), see [tls_insecure_set()](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php): "Configure verification of the server hostname in the server certificate."  
#### mqtt_v5
&ensp;'mqtt_v5': boolean, either true or false; set to true to use MQTT v5 (highest priority)  
#### mqtt_v311
&ensp;'mqtt_v311': boolean, either true or false; set to true to use MQTT v3.1.1 (second highest priority)  
#### mqtt_v31
&ensp;'mqtt_v31': boolean, either true or false; set to true to use MQTT v3.1.0 (least priority)  
#### mqtt_max_inflight_messages_set
&ensp;'mqtt_max_inflight_messages_set': a positive integer value; see [max_inflight_messages_set()](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php): "Set the maximum number of messages with QoS>0 that can be part way through their network flow at once.
Defaults to 20. Increasing this value will consume more memory but can increase throughput."

### (2) Modbus/MQTT template file in .csv format  
#### address
&ensp; 'address': see [address](https://github.com/namteckor/modbus-dl#address)  
#### read_type
&ensp; 'read_type': see [read_type](https://github.com/namteckor/modbus-dl#read_type)  
#### data_type
&ensp; 'data_type': see [data_type](https://github.com/namteckor/modbus-dl#data_type)  
#### tag_name
&ensp; 'tag_name': see [tag_name](https://github.com/namteckor/modbus-dl#tag_name)  
#### scaling_coeff
&ensp; 'scaling_coeff': see [scaling_coeff](https://github.com/namteckor/modbus-dl#scaling_coeff)  
#### scaling_offset
&ensp; 'scaling_offset': see [scaling_offset](https://github.com/namteckor/modbus-dl#scaling_offset)  
#### mqtt_topic
&ensp; 'mqtt_topic': string representing the topic to publish to, this will be prepended to the tag_name (can be empty)  
#### mqtt_payload
&ensp; 'mqtt_payload': currently supports "text" (just publish the value) and "json" (publish value with UTC and local timestamps); defaults to "text" if not specified  
#### mqtt_qos
&ensp; 'mqtt_qos': the Quality of Service (QoS) level to use; either 0 (at most once), 1 (at least once), or 2 (exactly once); defaults to 0 if not specified  
#### mqtt_retain
&ensp; 'mqtt_retain': a string of either "true" or "false"; whether (true) or not (false) to retain the message; defaults to true if not specified  
#### mqtt_publish
&ensp; 'mqtt_publish': a string defining the MQTT publish method; either "rbe" (report-by-exception), or a value representing the regular interval upload time in seconds; default to "rbe" if not specified  
#### mqtt_deadband
&ensp; 'mqtt_deadband': defines a deadband on the **scaled value** when reporting by exception; ignored by default for interval uploads/publish, use -f (--force-deadband) to force and apply the deadband logic with interval uploads/publish; defaults to 0 if none specified or unsupported, if data_type is 'di', 'coil' or 'packedbool', also if mqqt_publish is not rbe  
#### mqtt_alarm_low
&ensp; 'mqtt_alarm_low': defines a low alarm threshold on the **scaled value**; the scaled value will be published at each scan interval (regardless of mqtt_publish) as long as it remains below this threshold; defaults to None if not specified  
#### mqtt_alarm_high
&ensp; 'mqtt_alarm_high': defines a high alarm threshold on the **scaled value**; the scaled value will be published at each scan interval (regardless of mqtt_publish) as long as it remains above this threshold; defaults to None if not specified  
#### mqtt_ignore_low
&ensp; 'mqtt_ignore_low': completly ignore reporting and alarming while the **scaled value** remains below this threshold; defaults to None if not specified  
#### mqtt_ignore_high
&ensp; 'mqtt_ignore_high': completly ignore reporting and alarming while the **scaled value** remains above this threshold; defaults to None if not specified  

## Examples
### Basic authentication example
```text
./modqtt-gw.py -c config/modqtt_config_local.json -t template/modqtt_template_10.csv \
-e config/.env-local-broker
```
![Basic authentication example](../assets/modqtt-gw-basic-auth-example.png?raw=true)
### Certificates-based authentication example
```text
./modqtt-gw.py -c config/modqtt_config_local.json -t template/modqtt_template_10.csv \
-C /path/to/ca.crt \
-F /path/to/client.crt \
-K /path/to/client.key
```
![Certificates-based authentication example](../assets/modqtt-gw-certificates-based-auth-example.png?raw=true)
### Sample output
![Sample output](../assets/modqtt-gw-example.png?raw=true)