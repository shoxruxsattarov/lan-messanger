from __future__ import annotations

import json
from typing import Any, Dict


def encode_packet(packet: Dict[str, Any]) -> bytes:
    return (json.dumps(packet, ensure_ascii=False) + "\n").encode("utf-8")


def decode_packet(line: str) -> Dict[str, Any]:
    return json.loads(line)
