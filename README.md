# Onkyo IR Setup via MQTT

This project provides tools for recording and replaying Infrared (IR) command sequences for an Onkyo receiver over MQTT, utilizing a Tasmota-flashed IR sender.

## Architecture

The project consists of two primary scripts, a centralized YAML configuration, and python dependencies:

*   **`onkyo_setup.py`**: A player script. It interprets YAML-defined configurations and executes a specified set of IR sequences over an MQTT broker.
*   **`onkyo_record.py`**: A recorder script. It subscribes to your MQTT broker, watches for IR commands sent by your Tasmota device (or any device publishing matching NEC codes), and automatically formats and appends them into your configuration file.
*   **`config.yaml`**: The source of truth for your configuration, sequences, and named actions.
*   **`requirements.txt`**: Standard python package requirements file.

## Hardware Requirements

This project requires an **IR transceiver flashed with Tasmota**. The Tasmota device bridges the physical IR signals and MQTT, receiving commands from your physical remote (for the recording script) and transmitting them to the Onkyo receiver (for the playback script).

## Setup

First, ensure you have Python 3 installed. Then, install the required packages:

```bash
pip install -r requirements.txt
```

### Configuration (`config.yaml`)

Your `config.yaml` manages MQTT connection settings and defines macros.

```yaml
mqtt:
  host: <server>
  port: 1883
  topic: <topic>

sequences:
  my_custom_sequence:
    - [Power, 1]
    - [Down, 4]
    - [Right, 1]

actions:
  - name: Custom Setup
    sequences: [my_custom_sequence]
```

## Usage

### Replaying Actions

Use `onkyo_setup.py` to trigger actions. By default, running it without arguments will execute the action named **"All"**.

```bash
./onkyo_setup.py
```

To execute a specific action defined in your `config.yaml`, provide the action name as an argument. Note that the action name matching is case-insensitive.

```bash
./onkyo_setup.py "Factory Reset"
./onkyo_setup.py "Speakers Setup"
```

### Recording Sequences

Use `onkyo_record.py` to learn new macros by physically using your remote control and capturing the MQTT events. Provide a name for the new sequence as an argument.

```bash
./onkyo_record.py my_new_macro
```

The script will connect to the MQTT broker and listen for payloads matching known hex codes. As you press buttons on your remote, the script will output the detected commands and group consecutive identical commands together.

Press `Ctrl+C` to stop recording. The script will automatically format and append your recorded sequence to `config.yaml` under the `sequences` block.
