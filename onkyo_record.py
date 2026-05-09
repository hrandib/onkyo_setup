#!/usr/bin/env python3
import sys
import yaml
import signal
import paho.mqtt.client as mqtt
from onkyo_setup import COMMANDS

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <new_sequence_name>")
    sys.exit(1)

sequence_name = sys.argv[1]
sequence = []

# Reverse lookup for hex codes to command names
# We include both the full hex (e.g., 0xD207CB34) and without 0x (e.g., D207CB34)
DATA_TO_CMD = {v.lower(): k for k, v in COMMANDS.items()}
DATA_TO_CMD.update({v.replace("0x", "").lower(): k for k, v in COMMANDS.items()})

# PyYAML helper to format [Cmd, Repeats] inline (Flow style)
class FlowList(list):
    pass

def flow_list_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

yaml.SafeDumper.add_representer(FlowList, flow_list_rep)

def save_sequence():
    if not sequence:
        print("\nNo commands recorded. Exiting without saving.")
        sys.exit(0)

    print(f"\nSaving sequence '{sequence_name}' to config.yaml...")
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    if "sequences" not in config:
        config["sequences"] = {}

    # Format the sequence, keeping commands with 1 repeat as simple strings
    formatted_seq = []
    for cmd, repeats in sequence:
        if repeats == 1:
            formatted_seq.append(cmd)
        else:
            formatted_seq.append(FlowList([cmd, repeats]))

    config["sequences"][sequence_name] = formatted_seq

    # Ensure all other sequences also use the compact formatting
    for seq_name, seq_data in config.get("sequences", {}).items():
        if isinstance(seq_data, list):
            new_seq_data = []
            for item in seq_data:
                if isinstance(item, list):
                    if len(item) == 2 and item[1] == 1:
                        new_seq_data.append(item[0])
                    else:
                        new_seq_data.append(FlowList(item))
                else:
                    new_seq_data.append(item)
            config["sequences"][seq_name] = new_seq_data

    with open("config.yaml", "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

    print("Done!")
    sys.exit(0)

def signal_handler(sig, frame):
    save_sequence()

signal.signal(signal.SIGINT, signal_handler)

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected to MQTT broker.")
    topic = userdata.get('topic')

    # Deriving Tasmota's standard tele/+/RESULT topic from the cmnd topic
    tele_topic = topic.replace("cmnd/", "tele/").rsplit("/", 1)[0] + "/RESULT" if "cmnd/" in topic else "tele/+/RESULT"

    print(f"Subscribing to {topic} and {tele_topic} for IR commands... (Press Ctrl+C to finish)")
    client.subscribe(topic)
    client.subscribe(tele_topic)

def on_connect_v1(client, userdata, flags, rc):
    # Compatibility wrapper for paho-mqtt v1.x
    on_connect(client, userdata, flags, rc)

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8').lower()

    # Try to find a known command in the payload
    found_cmd = None
    for data, cmd in DATA_TO_CMD.items():
        if data in payload:
            found_cmd = cmd
            break

    if found_cmd:
        # If it's the same command as the last one, increment the repeat counter
        if sequence and sequence[-1][0] == found_cmd:
            sequence[-1][1] += 1
            print(f"\rRecorded: {found_cmd} x{sequence[-1][1]}", end="", flush=True)
        else:
            sequence.append([found_cmd, 1])
            print(f"\nRecorded: {found_cmd} x1", end="", flush=True)

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    mqtt_cfg = config.get('mqtt', {})
    mqtt_host = mqtt_cfg.get('host', 'localhost')
    mqtt_port = mqtt_cfg.get('port', 1883)

    mqtt_topic = mqtt_cfg.get('topic')
    if not mqtt_topic:
        print("Error: MQTT topic is missing in config.yaml")
        sys.exit(1)

    try:
        from paho.mqtt.enums import CallbackAPIVersion
        client = mqtt.Client(CallbackAPIVersion.VERSION2, userdata={'topic': mqtt_topic})
        client.on_connect = on_connect
    except ImportError:
        client = mqtt.Client(userdata={'topic': mqtt_topic})
        client.on_connect = on_connect_v1

    client.on_message = on_message

    print(f"Connecting to {mqtt_host}:{mqtt_port}...")
    client.connect(mqtt_host, mqtt_port)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
