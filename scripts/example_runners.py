# Copyright (c) 2026 Daniel Ari Friedman
"""Thin YAML/CLI boundary that dispatches typed reusable scientific examples."""

import argparse
import sys
from pathlib import Path
from typing import assert_never

import yaml
from pydantic import JsonValue
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from antropy_hd.errors import ParameterError
from scripts.example_alphabet import run_alphabet
from scripts.example_inference import run_inference
from scripts.example_models import (
    AlphabetPlan,
    ExampleKind,
    InferencePlan,
    PlanningPlan,
    SpatialPlan,
)
from scripts.example_planning import run_planning
from scripts.example_reports import ExampleReport
from scripts.example_spatial import run_spatial


def _unique_mapping_keys(node: Node, visited: set[int]) -> None:
    """Reject duplicate or non-string keys at every YAML mapping depth."""
    if id(node) in visited:
        raise ParameterError("plan", "YAML aliases are not supported")
    visited.add(id(node))
    if isinstance(node, MappingNode):
        keys: set[str] = set()
        for key, value in node.value:
            if not isinstance(key, ScalarNode) or key.tag != "tag:yaml.org,2002:str":
                raise ParameterError("plan", "YAML mapping keys must be literal strings")
            if key.value in keys:
                raise ParameterError("plan", f"duplicate YAML key: {key.value}")
            _unique_mapping_keys(key, visited)
            keys.add(key.value)
            _unique_mapping_keys(value, visited)
        return
    if isinstance(node, SequenceNode):
        for value in node.value:
            _unique_mapping_keys(value, visited)


def read_example_yaml(path: Path) -> JsonValue:
    """Parse safe YAML with explicit unique settings and no alias expansion."""
    source = path.read_text(encoding="utf-8")
    try:
        loader = yaml.SafeLoader(source)
        node = loader.get_single_node()
        if node is not None:
            _unique_mapping_keys(node, set())
        return yaml.safe_load(source)
    except yaml.YAMLError as error:
        raise ParameterError("plan", f"invalid YAML: {error}") from error


def run_example(kind: ExampleKind, plan_path: Path) -> ExampleReport:
    """Load strict YAML and dispatch one matching immutable scientific plan."""
    data = read_example_yaml(plan_path)
    match kind:
        case ExampleKind.SPATIAL:
            return run_spatial(SpatialPlan.model_validate(data))
        case ExampleKind.ALPHABET:
            return run_alphabet(AlphabetPlan.model_validate(data))
        case ExampleKind.PLANNING:
            return run_planning(PlanningPlan.model_validate(data))
        case ExampleKind.INFERENCE:
            return run_inference(InferencePlan.model_validate(data))
        case unreachable:
            assert_never(unreachable)


def example_main(kind: ExampleKind, default_plan: Path) -> None:
    """Accept a plan path and emit exactly one computed strict JSON object."""
    parser = argparse.ArgumentParser(
        description=f"Run the {kind.value} example from a strict YAML plan"
    )
    _ = parser.add_argument("--plan", type=Path, default=default_plan, help="YAML control file")
    arguments = parser.parse_args()
    plan_path: Path = arguments.plan
    report = run_example(kind, plan_path)
    _ = sys.stdout.write(report.model_dump_json() + "\n")
