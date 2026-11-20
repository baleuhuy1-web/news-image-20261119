#!/usr/bin/env python3
"""Hand the finished front page to the grading harness.

The picture itself is rendered ahead of time by build_image.py and kept
beside this file as entry.png.  At run time this program only has to put a
copy of that file where the harness looks for it: entry.png inside the
directory given by MAKEFUN_OUTPUT_DIR, or /output when that variable is
not set.  Before copying it checks the file really is a PNG, is within the
size limit and is no larger than 1024x1024; after copying it reads both
files back and refuses to finish unless they match byte for byte.  Only
the Python standard library is used, and nothing here touches the network.
"""

import os
import shutil
import struct
import sys

PICTURE = "entry.png"
FALLBACK_DIR = "/output"
MAGIC = b"\x89PNG\r\n\x1a\n"
SIZE_LIMIT = 1_048_576
EDGE_LIMIT = 1024


def validate(path):
    """Check the picture's limits; return a message or None when it is fine."""
    if os.path.getsize(path) > SIZE_LIMIT:
        return f"{PICTURE} is over the {SIZE_LIMIT}-byte limit"
    with open(path, "rb") as handle:
        opening = handle.read(24)
    if len(opening) < 24 or not opening.startswith(MAGIC):
        return f"{PICTURE} does not start with a PNG signature"
    # Width and height sit in the IHDR chunk as big-endian 32-bit values
    # at byte offsets 16 and 20.
    wide, tall = struct.unpack(">II", opening[16:24])
    if wide > EDGE_LIMIT or tall > EDGE_LIMIT:
        return f"{PICTURE} is {wide}x{tall}, over {EDGE_LIMIT}px"
    return None


def same_bytes(first, second):
    with open(first, "rb") as a, open(second, "rb") as b:
        return a.read() == b.read()


def run():
    folder = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(folder, PICTURE)
    if not os.path.isfile(source):
        print(f"error: {PICTURE} is missing next to main.py", file=sys.stderr)
        return 1
    fault = validate(source)
    if fault:
        print(f"error: {fault}", file=sys.stderr)
        return 1

    target_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or FALLBACK_DIR
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, PICTURE)
    shutil.copyfile(source, target)
    if not same_bytes(source, target):
        print("error: the copy is not identical to the original",
              file=sys.stderr)
        return 1
    print(f"wrote {target} ({os.path.getsize(target)} bytes, verified)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
