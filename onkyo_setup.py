#!/usr/bin/env python3
import argparse
import json
import time
import yaml
import paho.mqtt.client as mqtt

# --- Variable Definitions ---
COMMANDS = {
    "Power": "0xD207CB34",
    "Dim1": "0xD206956A",
    "Dim2": "0xD2069669",
    "Dim3": "0xD2069768",
    "Down": "0xD2079B64",
    "Left": "0xD2079F60",
    "Right": "0xD2079E61",
    "Setup": "0xD20753AC",
    "Up": "0xD2079A65",
    "Value_increment": "0xD2079C63",
    "Value_decrement": "0xD2079D62",
    "Volume_increment": "0xD20602FD",
    "Volume_decrement": "0xD20603FC",
}

def send_cmd(client, topic, cmd_name, repeats=1):
    data_lsb = COMMANDS[cmd_name]
    payload = {
        "Protocol": "NEC",
        "Bits": 32,
        "DataLSB": data_lsb,
        "Repeat": 0
    }

    for _ in range(repeats):
        print(f"Sending {cmd_name}...")

        # Publish the JSON payload via MQTT
        client.publish(topic, json.dumps(payload), qos=0)
        time.sleep(0.5)

class Action:
    def __init__(self, name, sequences=None):
        self.name = name
        # An Action contains a set of sequences
        self.sequences = sequences if sequences is not None else []

    def add_sequence(self, sequence):
        self.sequences.append(sequence)

    def execute(self, client, topic):
        print(f"=== Executing Action: {self.name} ===")
        for sequence in self.sequences:
            for item in sequence:
                if isinstance(item, list) and len(item) == 2:
                    cmd, repeats = item
                else:
                    cmd, repeats = item, 1
                send_cmd(client, topic, cmd, repeats)
        print(f"=== Finished Action: {self.name} ===")

def load_actions(config):
    sequences_map = config.get('sequences', {})
    actions_config = config.get('actions', [])

    actions = []
    for act_conf in actions_config:
        seq_names = act_conf.get('sequences', [])
        loaded_sequences = []
        for sn in seq_names:
            if sn in sequences_map:
                loaded_sequences.append(sequences_map[sn])
        actions.append(Action(act_conf.get('name'), loaded_sequences))

    return actions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Onkyo IR setup sequences.")
    parser.add_argument("action", nargs="?", default="All", help="Action name to execute (default: 'All')")
    args = parser.parse_args()

    # Load configuration
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    mqtt_cfg = config.get('mqtt', {})
    mqtt_host = mqtt_cfg.get('host', 'localhost')
    mqtt_port = mqtt_cfg.get('port', 1883)

    mqtt_topic = mqtt_cfg.get('topic')
    if not mqtt_topic:
        print("Error: MQTT topic not specified in configuration.")
        exit(1)

    # Initialize MQTT client
    try:
        # Handle paho-mqtt >= 2.0.0
        from paho.mqtt.enums import CallbackAPIVersion
        client = mqtt.Client(CallbackAPIVersion.VERSION2)
    except ImportError:
        # Handle paho-mqtt < 2.0.0
        client = mqtt.Client()

    client.connect(mqtt_host, mqtt_port)
    client.loop_start()

    actions = load_actions(config)

    action_to_run = None
    for action in actions:
        if action.name.lower() == args.action.lower():
            action_to_run = action
            break

    if action_to_run:
        action_to_run.execute(client, mqtt_topic)
    else:
        print(f"Error: Action '{args.action}' not found in configuration.")
        available_actions = [a.name for a in actions]
        print(f"Available actions: {', '.join(available_actions)}")

    # Cleanup background thread and disconnect
    client.loop_stop()
    client.disconnect()
