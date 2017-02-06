# json2mqtt Proxy server

json2mqtt is a simple http proxy server to receive JSON via POST requests, and push it to an MQTT server that it is subscribed to. It can be configured to match personal needs using the `config.ini` file, and can be daemonized using standard shell foo.

```bash
pip install -r requirements.txt
python json2mqtt.py &
```

