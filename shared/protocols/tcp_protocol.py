import json
import socket
import struct
from typing import Optional

from shared.protocols.constants import HEADER_SIZE, MAX_MESSAGE_SIZE


class ProtocolError(Exception):
    pass


def encode_message(data: dict) -> bytes:
    payload = json.dumps(data).encode("utf-8")
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ProtocolError(
            f"Message size {len(payload)} exceeds maximum {MAX_MESSAGE_SIZE}"
        )
    header = struct.pack("!I", len(payload))
    return header + payload


def decode_header(header_bytes: bytes) -> int:
    if len(header_bytes) != HEADER_SIZE:
        raise ProtocolError(
            f"Header must be {HEADER_SIZE} bytes, got {len(header_bytes)}"
        )
    (length,) = struct.unpack("!I", header_bytes)
    if length > MAX_MESSAGE_SIZE:
        raise ProtocolError(
            f"Payload size {length} exceeds maximum {MAX_MESSAGE_SIZE}"
        )
    return length


def decode_payload(payload_bytes: bytes) -> dict:
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ProtocolError(f"Failed to decode payload: {e}")
    if not isinstance(data, dict):
        raise ProtocolError(f"Payload must be a JSON object, got {type(data).__name__}")
    return data


def _recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            if len(buf) == 0:
                return None  # clean close
            raise ProtocolError(
                f"Connection closed mid-read: got {len(buf)} of {n} bytes"
            )
        buf.extend(chunk)
    return bytes(buf)


def send_message(sock: socket.socket, data: dict) -> None:
    raw = encode_message(data)
    sock.sendall(raw)


def recv_message(sock: socket.socket) -> Optional[dict]:
    header_bytes = _recv_exact(sock, HEADER_SIZE)
    if header_bytes is None:
        return None  # clean close
    length = decode_header(header_bytes)
    payload_bytes = _recv_exact(sock, length)
    if payload_bytes is None:
        raise ProtocolError("Connection closed while reading payload")
    return decode_payload(payload_bytes)
