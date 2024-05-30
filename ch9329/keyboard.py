from __future__ import annotations

import time
from typing import List
from typing import Literal
from typing import Tuple

from serial import Serial

from ch9329.exceptions import InvalidKey
from ch9329.exceptions import InvalidModifier
from ch9329.hid import HID_MAPPING
from ch9329.utils import get_packet

Modifier = Literal[
    "ctrl",
    "ctrl_left",
    "ctrl_right",
    "shift",
    "shift_left",
    "shift_right",
    "alt",
    "alt_left",
    "alt_right",
    "win",
    "win_left",
    "win_right",
]

MODIFIER_MAP = {
    "ctrl": 0b00000001,
    "ctrl_left": 0b00000001,
    "shift": 0b00000010,
    "shift_left": 0b00000010,
    "alt": 0b00000100,
    "alt_left": 0b00000100,
    "win": 0b00001000,
    "win_left": 0b00001000,
    "ctrl_right": 0b00010000,
    "shift_right": 0b00100000,
    "alt_right": 0b01000000,
    "win_right": 0b10000000,
}

# Convert character to data packet
HEAD = b"\x57\xab"  # Frame header
ADDR = b"\x00"  # Address
CMD = b"\x02"  # Command
LEN = b"\x08"  # Data length


def send(
    ser: Serial,
    keys: Tuple[str, str, str, str, str, str] = ("", "", "", "", "", ""),
    modifiers: List[Modifier] = [],
) -> None:
    # CMD_SEND_KB_GENERAL_DATA data has exactly 8 bytes
    data = b""

    # first byte modifiers key, each bit represents 1 key
    #
    # BIT0 - ctrl_left
    # BIT1 - shift_left
    # BIT2 - alt_left
    # BIT3 - win_left
    # BIT4 - ctrl_right
    # BIT5 - shift_right
    # BIT6 - alt_right
    # BIT7 - win_right
    modifier = 0x00
    for m in modifiers:
        if m not in MODIFIER_MAP:
            raise InvalidModifier(m)
        modifier |= MODIFIER_MAP[m]
    data += modifier.to_bytes(1, byteorder="little")

    # second byte must be 0x00
    data += b"\x00"

    # third to eigth bytes are keys
    # we can press upto 6 buttons
    for key in keys:
        if key not in HID_MAPPING:
            raise InvalidKey(key)
        hid, _ = HID_MAPPING[key]
        data += hid

    # create packet and send
    packet = get_packet(HEAD, ADDR, CMD, LEN, data)
    ser.write(packet)


def press(ser: Serial, key: str, modifiers: List[Modifier] = []) -> None:
    send(ser, (key, "", "", "", "", ""), modifiers)


def release(ser: Serial) -> None:
    send(ser, ("", "", "", "", "", ""))


def press_and_release(
    ser: Serial, key: str, modifiers: List[Modifier] = []
) -> None:
    press(ser, key, modifiers)
    release(ser)


def write(ser: Serial, text: str, interval: float = 0.1) -> None:
    for char in text:
        if char not in HID_MAPPING:
            raise InvalidKey(char)
        _, shift = HID_MAPPING[char]
        press_and_release(ser, char, ["shift"] if shift else [])
        time.sleep(interval)
