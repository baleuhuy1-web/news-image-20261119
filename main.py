#!/usr/bin/env python3
"""Deliver entry.png to the output directory named by MAKEFUN_OUTPUT_DIR.

Standard library only. The image is validated before it is copied and the
copy is checked byte-for-byte afterwards, so a bad or truncated file can
never be delivered silently.
"""

import hashlib
import os
import shutil
import struct
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
MAX_SIDE = 1024


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def check_image(path):
    """Validate the PNG: signature, size, and IHDR dimensions."""
    try:
        with open(path, "rb") as handle:
            blob = handle.read()
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")

    if len(blob) < 8 or blob[:8] != PNG_MAGIC:
        fail(f"{path} is not a PNG file")
    if len(blob) > MAX_BYTES:
        fail(f"{path} is {len(blob)} bytes, over the {MAX_BYTES} byte limit")
    if len(blob) < 24 or blob[12:16] != b"IHDR":
        fail(f"{path} has no IHDR chunk")
    width, height = struct.unpack(">II", blob[16:24])
    if width > MAX_SIDE or height > MAX_SIDE:
        fail(f"{path} is {width}x{height}, over the {MAX_SIDE}x{MAX_SIDE} limit")
    return blob


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    source_bytes = check_image(source)

    target_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as exc:
        fail(f"cannot create {target_dir}: {exc}")

    destination = os.path.join(target_dir, "entry.png")
    try:
        shutil.copyfile(source, destination)
    except OSError as exc:
        fail(f"cannot copy to {destination}: {exc}")

    try:
        with open(destination, "rb") as handle:
            delivered = handle.read()
    except OSError as exc:
        fail(f"cannot read back {destination}: {exc}")

    if digest(delivered) != digest(source_bytes):
        fail(f"{destination} does not match {source} byte-for-byte")

    print(f"delivered {destination} ({len(delivered)} bytes)")


if __name__ == "__main__":
    main()
