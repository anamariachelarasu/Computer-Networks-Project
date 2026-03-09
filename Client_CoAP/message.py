import json
import random

# Constante
V1 = 1

# Message Types
TYPE_CONFIRMABLE = 0
TYPE_NONCONFIRMABLE = 1
TYPE_ACKNOWLEDGEMENT = 2
TYPE_RESET = 3

# Method Codes
CODE_CREATE = 1
CODE_GET = 2
CODE_DELETE = 3
CODE_MOVE = 4
CODE_EDIT = 5


def message_init(token=b"", payload=b"", message_id=None):
    return {
        "version": V1,
        "type": TYPE_CONFIRMABLE,
        "code": CODE_GET,
        "token": token,
        "tkl": len(token),
        "message_id": message_id if message_id is not None else random.randint(0, 65535),
        "payload": payload
    }


def encode_message(msg):
    packet = bytearray()

    # Header: Ver(2 bits) | T(2 bits) | TKL(4 bits)
    first_byte = (msg["version"] << 6) | (msg["type"] << 4) | (msg["tkl"] & 0x0f)
    packet.append(first_byte)

    packet.append(msg["code"])
    packet.append((msg["message_id"] >> 8) & 0xff)
    packet.append(msg["message_id"] & 0xff)

    packet.extend(msg["token"])

    if msg["payload"]:
        packet.append(0xff)  # Payload marker
        packet.extend(msg["payload"])

    return packet


def decode_message(buffer):
    if not isinstance(buffer, bytearray):
        buffer = bytearray(buffer)
    if len(buffer) < 4:
        return None

    tkl = buffer[0] & 0x0F
    code_val = buffer[1]
    msg_id = (buffer[2] << 8) | buffer[3]
    token = buffer[4:4 + tkl]

    payload = b""
    if 0xFF in buffer:
        idx = buffer.index(0xFF)
        payload = buffer[idx + 1:]

    msg = message_init(token=token, payload=payload, message_id=msg_id)
    msg["code"] = code_val
    msg["type"] = (buffer[0] >> 4) & 0x03

    return msg

def fragment_payload(full_content, chunk_size = 500):
    fragments = []

    # Daca continutul este gol, returnam un singur fragment gol
    if not full_content:
        return [""]

    for i in range(0, len(full_content), chunk_size):
        fragments.append(full_content[i:i + chunk_size])
    return fragments

def create_fragmented_payload(fragment_current, fragment_total, **kwargs):
    kwargs['fragment_current'] = fragment_current
    kwargs['fragment_total'] = fragment_total
    return json.dumps(kwargs).encode("utf-8")

def create_payload(**kwargs):
    return json.dumps(kwargs).encode("utf-8")
