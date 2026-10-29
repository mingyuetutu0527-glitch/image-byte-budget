#!/usr/bin/env python3
"""Byte-budget arithmetic for upload limits.

No models, no estimates: this only converts units and subtracts known request
overhead, so that the number you type into a compressor is one the form on the
other side will actually accept.

Examples
--------
    # A form says 10 MB and posts the file as base64 inside JSON
    python byte_budget.py --limit "10 MB" --transport base64-json

    # Same limit, ordinary multipart form
    python byte_budget.py --limit "10 MB" --transport multipart

    # What does typing 2000 KB into a compressor produce, against a 2 MB limit?
    python byte_budget.py --target "2000 KB" --limit "2 MB"

    # Show every transport for a limit
    python byte_budget.py --limit "2 MB" --all
"""

import argparse
import math

# Measured on one real form (see data/upload-error-triage.md):
# base64-in-JSON wrapper cost 85 bytes; multipart boundaries cost 183-198 bytes.
BASE64_JSON_WRAPPER = 85
MULTIPART_OVERHEAD = {"best": 183, "worst": 198}

UNITS = {
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
    "KIB": 1024,
    "MIB": 1024 ** 2,
    "GIB": 1024 ** 3,
}


def parse_size(text):
    """Parse '10 MB', '2000KB', '1.5 MiB' into bytes using binary units."""
    parts = text.strip().replace(",", "").split()
    if len(parts) == 1:
        # allow '10MB'
        digits = "".join(ch for ch in parts[0] if ch.isdigit() or ch == ".")
        unit = parts[0][len(digits):] or "B"
        number = float(digits)
    else:
        number = float(parts[0])
        unit = parts[1]
    unit = unit.upper()
    if unit not in UNITS:
        raise SystemExit(f"unknown unit {unit!r}; known: {', '.join(sorted(UNITS))}")
    return int(number * UNITS[unit])


def decimal_bytes(text):
    """The same string read with decimal prefixes (KB = 1,000, MB = 1,000,000)."""
    parts = text.strip().replace(",", "").split()
    if len(parts) == 1:
        digits = "".join(ch for ch in parts[0] if ch.isdigit() or ch == ".")
        unit = (parts[0][len(digits):] or "B").upper()
        number = float(digits)
    else:
        number, unit = float(parts[0]), parts[1].upper()
    power = {"B": 0, "KB": 1, "MB": 2, "GB": 3}.get(unit)
    if power is None:
        return None
    return int(number * (1000 ** power))


def max_file_base64_json(limit_bytes, wrapper=BASE64_JSON_WRAPPER):
    """Largest file whose base64 encoding plus wrapper still fits the limit."""
    budget = limit_bytes - wrapper
    if budget <= 0:
        return 0
    return (budget // 4) * 3


def max_file_multipart(limit_bytes, overhead):
    return max(0, limit_bytes - overhead)


def kb_to_type(max_bytes):
    """The largest whole KB value that stays under max_bytes (KB = 1024)."""
    return max_bytes // 1024


def report(limit_text, transport, wrapper, target_text=None, limit_base="decimal"):
    binary = parse_size(limit_text)
    decimal = decimal_bytes(limit_text)
    if limit_base == "binary":
        limit = binary
    elif limit_base == "decimal":
        limit = decimal if decimal is not None else binary
    else:
        raise SystemExit("--limit-base must be decimal or binary")
    other = binary if limit == decimal else decimal
    print(f"limit            {limit_text} = {limit:,} bytes ({limit_base} prefixes)")
    if other is not None and other != limit:
        print(f"                 the other reading: {other:,} bytes "
              f"({(other - limit) / limit * 100:+.4f}%)")

    if target_text:
        tgt = parse_size(target_text)
        print(f"target           {target_text} = {tgt:,} bytes")
        if tgt > limit:
            print(f"                 over the limit by {tgt - limit:,} bytes")
        else:
            print(f"                 under the limit by {limit - tgt:,} bytes")

    transports = ["multipart", "base64-json"] if transport == "all" else [transport]
    for name in transports:
        print()
        if name == "multipart":
            for label, overhead in MULTIPART_OVERHEAD.items():
                room = max_file_multipart(limit, overhead)
                print(f"multipart ({label:5s}) overhead {overhead} B -> "
                      f"file <= {room:,} bytes ({kb_to_type(room):,} KB to type)")
        else:
            room = max_file_base64_json(limit, wrapper)
            print(f"base64+json      wrapper {wrapper} B -> file <= {room:,} bytes "
                  f"({kb_to_type(room):,} KB to type)")
            print(f"                 base64 length {math.ceil(room / 3) * 4:,} B, "
                  f"body {math.ceil(room / 3) * 4 + wrapper:,} B")


def main():
    ap = argparse.ArgumentParser(description="Upload byte-budget arithmetic.")
    ap.add_argument("--limit", help='form limit, e.g. "10 MB" or "2 MB"')
    ap.add_argument("--target", help='what you plan to type, e.g. "2000 KB"')
    ap.add_argument("--transport", default="multipart",
                    choices=["multipart", "base64-json", "all"])
    ap.add_argument("--limit-base", default="decimal", choices=["decimal", "binary"],
                    help="how the form reads MB: 1,000,000 (decimal, default) or 1,048,576 (binary)")
    ap.add_argument("--wrapper", type=int, default=BASE64_JSON_WRAPPER,
                    help="bytes of JSON wrapper around the base64 string (default 85, measured)")
    args = ap.parse_args()

    if not args.limit:
        ap.error("--limit is required")

    report(args.limit, args.transport, args.wrapper, args.target, args.limit_base)


if __name__ == "__main__":
    main()
