#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd>=0.2", "pyyaml>=6"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# Copyright (c) 2026 Daniel Ari Friedman
"""Run the alphabet example from explicit YAML controls and emit strict JSON."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.example_models import ExampleKind
from scripts.example_runners import example_main

if __name__ == "__main__":
    example_main(
        ExampleKind.ALPHABET, Path(__file__).resolve().parent / "configs" / "alphabet.yaml"
    )
