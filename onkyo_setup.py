#!/usr/bin/env python3
import json
import time
import subprocess

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
    "Val_inc": "0xD2079C63",
    "Val_dec": "0xD2079D62",
    "Vol_inc": "0xD20602FD",
    "Vol_dec": "0xD20603FC",
}

def send_cmd(cmd_name, repeats=1):
    data_lsb = COMMANDS[cmd_name]
    payload = {
        "Protocol": "NEC",
        "Bits": 32,
        "DataLSB": data_lsb,
        "Repeat": 0
    }
    
    for _ in range(repeats):
        print(f"Sending {cmd_name}...")
        
        # Using subprocess.run with a list of arguments ensures that 
        # the JSON payload is passed as a single argument and properly escaped.
        subprocess.run([
            "mosquitto_pub",
            "-h", "serv.lan",
            "-p", "1883",
            "-t", "cmnd/ir2/irsend",
            "-m", json.dumps(payload),
            "-q", "0"
        ])
        time.sleep(0.5)

if __name__ == "__main__":
    # --- Recorded Message Sequence ---
    sequence = [
        ("Power", 1),
        ("Dim1", 2),
        ("Setup", 1),
        ("Right", 1),
        ("Down", 2),
        ("Val_dec", 1),
        ("Down", 1),
        ("Val_dec", 1),
        ("Down", 2),
        ("Left", 1),
        ("Down", 2),
        ("Right", 1),
        ("Down", 4),
        ("Val_dec", 2),
        ("Up", 1),
        ("Down", 1),
        ("Val_inc", 8),
        ("Down", 1),
        ("Val_inc", 6),
        ("Down", 1),
        ("Val_inc", 7),
        ("Down", 1),
        ("Left", 1),
        ("Up", 1),
        ("Right", 1),
        ("Down", 4),
        ("Val_inc", 2),
        ("Down", 1),
        ("Val_inc", 2),
        ("Down", 1),
        ("Val_inc", 10),
        ("Down", 1),
        ("Setup", 1),
        ("Vol_inc", 35),
        ("Power", 1)
    ]

    for cmd, repeats in sequence:
        send_cmd(cmd, repeats)
