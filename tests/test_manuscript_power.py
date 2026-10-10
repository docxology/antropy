# Copyright (c) 2026 Daniel Ari Friedman
"""Real prospective producers drive manuscript values, tables, figures and rejection controls."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest
import yaml
from pypdf import PdfReader

from antropy_hd.errors import ParameterError
from scripts.build_manuscript import build
from scripts.manuscript_claims import write_claims
from scripts.manuscript_data import file_sha256, read_data
from scripts.manuscript_hydration import section_texts
from scripts.manuscript_power import power_variables, resolution_restrictions
from scripts.manuscript_power_tables import effect_table, interval_text, operating_tables
from scripts.manuscript_profile import load_context
from scripts.manuscript_variables import publication_variables
from scripts.power_models import PowerReport
from scripts.run_experiments import execute_experiments
from scripts.validate_power import validate_power
from tests.artifact_fixtures import prepare_project
from tests.test_power_validation import small_power as small_power  # noqa: PLC0414


@pytest.fixture(scope="module")
def power_publication(tmp_path_factory: pytest.TempPathFactory, small_power: Path) -> Path:
    root = tmp_path_factory.mktemp("power-manuscript") / "project"
    plan = prepare_project(root)
    _ = execute_experiments(root, plan)
    _ = shutil.copytree(small_power / "output/power", root / "output/power")
    _ = shutil.copyfile(small_power / "power_plan.yaml", root / "power_plan.yaml")
    path = root / "docs/manuscript/project.yaml"
    profile = yaml.safe_load(path.read_text())
    profile["power_required"] = True
    _ = path.write_text(yaml.safe_dump(profile, sort_keys=False))
    return root


def report(root: Path) -> PowerReport:
    return PowerReport.model_validate_json((root / "output/power/report.json").read_bytes())


def test_power_values_are_sourced_from_complete_producer_records(power_publication: Path) -> None:
    actual = validate_power(power_publication)
    values = power_variables(power_publication, actual, 6)
    assert values["POWER_FIELDS"] == str(actual.plan.field_count)
    assert values["POWER_DECISIONS"] == str(actual.plan.experiment_count)
    assert values["POWER_SUMMARIES"] == str(
        len(actual.plan.shapes)
        * len(actual.plan.scenarios)
        * len(actual.plan.sample_sizes)
        * len(actual.plan.analyses)
    )
    available = sum(item.status == "available" for item in actual.experiments)
    assert int(values["POWER_AVAILABLE"]) == available
    assert int(values["POWER_UNAVAILABLE"]) == len(actual.experiments) - available > 0
    assert values["POWER_REPORT_SHA256"] == file_sha256(
        power_publication / "output/power/report.json"
    )
    assert str(actual.resources.peak_pool_bytes) in values["POWER_RESOURCE_TABLE"]
    assert str(actual.plan.max_report_bytes) in values["POWER_PLAN_TABLE"]
    assert str(actual.plan.test.resamples) in values["POWER_TEST_TABLE"]


def test_every_operating_cell_and_undefined_denominator_is_retained(
    power_publication: Path,
) -> None:
    actual = report(power_publication)
    values = operating_tables(actual, 6)
    for table in values.values():
        row_count = sum(line.startswith("| ") for line in table.splitlines())
        assert row_count - len(actual.plan.scenarios) == len(actual.summaries)
        assert all(scenario.label in table for scenario in actual.plan.scenarios)
        assert all(analysis.label in table for analysis in actual.plan.analyses)
    unavailable = [row for row in actual.summaries if row.available == 0]
    assert unavailable
    assert all(interval_text(row.conditional_rejection, 6) == "undefined" for row in unavailable)
    assert "undefined" in values["POWER_AVAILABILITY_TABLE"]
    assert all(row.conditional_rejection.estimate is None for row in unavailable)


def test_caption_has_null_only_calibration_and_consumed_design(power_publication: Path) -> None:
    context = load_context(power_publication)
    data = read_data(power_publication, context)
    values = publication_variables(power_publication, context, data)
    assert data.power is not None
    null_label = next(item.label for item in data.power.plan.scenarios if item.role == "null")
    alternative_label = next(
        item.label for item in data.power.plan.scenarios if item.role == "alternative"
    )
    caption = values["POWER_AVAILABILITY_FIGURE"]
    assert null_label in caption
    assert alternative_label not in caption
    assert "Raw rejection" in caption
    assert data.power.plan.multiplicity in caption
    assert values["POWER_REPETITIONS"] in caption
    assert values["POWER_CONFIDENCE"] in caption
    assert "{{" not in "\n".join(section_texts(power_publication, context, values))


def test_exact_resolution_uses_complementary_allocations_and_declared_family(
    power_publication: Path,
) -> None:
    actual = report(power_publication)
    text = resolution_restrictions(actual, 6)
    # Count labeled allocations independently of the stored scheduling formula.
    exact_n = min(actual.plan.sample_sizes)
    assert format(2 / math.comb(2 * exact_n, exact_n), ".6g") in text
    assert format(actual.plan.alpha / len(actual.plan.analyses), ".6g") in text
    assert "precluded" in text
    assert "70" not in text  # The larger sampled schedule is not asserted to be exact.
    payload = actual.model_dump(mode="json")
    payload["plan"]["multiplicity"] = "none"
    unadjusted = resolution_restrictions(PowerReport.model_validate(payload), 6)
    assert "unadjusted threshold" in unadjusted
    assert "0.05" in unadjusted
    payload["resources"]["schedules"] = [
        item for item in payload["resources"]["schedules"] if item["method"] == "monte_carlo"
    ]
    assert "sampled allocations" in resolution_restrictions(PowerReport.model_validate(payload), 6)
    payload["plan"]["test"]["alternative"] = "greater"
    assert "configured tail" in resolution_restrictions(PowerReport.model_validate(payload), 6)


def test_explicit_no_power_data_asserts_no_power_results(tmp_path: Path) -> None:
    root = tmp_path / "project"
    plan = prepare_project(root)
    _ = execute_experiments(root, plan)
    context = load_context(root)
    data = read_data(root, context)
    assert data.power is None
    values = publication_variables(root, context, data)
    assert "disabled" in values["POWER_NARRATIVE"]
    assert "omitted" in values["POWER_REJECTION_FIGURE"]
    assert "{{" not in "\n".join(section_texts(root, context, values))


@pytest.mark.parametrize("rows", [[("1",)], [("1",) * 8]])
def test_effect_table_rejects_incomplete_or_extra_columns(rows: list[tuple[str, ...]]) -> None:
    with pytest.raises(ParameterError):
        effect_table(("Shape", "n", "Method", "Mean", "SD", "Raw", "Adjusted"), rows)


def test_claims_bind_real_power_csvs_and_inference_sources(power_publication: Path) -> None:
    context = load_context(power_publication)
    write_claims(power_publication, read_data(power_publication, context))
    payload = json.loads((power_publication / "docs/manuscript/claims.json").read_text())
    claims = {item["id"]: item["sources"] for item in payload["claims"]}
    assert {"power-design", "power-estimates", "inference-method"} <= claims.keys()
    assert "output/power/decisions.csv" in claims["power-estimates"]
    assert "output/power/summary.csv" in claims["power-estimates"]
    assert all((power_publication / source).is_file() for source in claims["power-estimates"])


def test_corrupt_power_fails_before_publication_writes(
    tmp_path: Path, power_publication: Path
) -> None:
    root = tmp_path / "project"
    _ = shutil.copytree(power_publication, root)
    path = root / "output/power/report.json"
    payload = json.loads(path.read_text())
    payload["summaries"].pop()
    _ = path.write_text(json.dumps(payload))
    source = root / "docs/manuscript/manuscript.md"
    original = source.read_bytes()
    with pytest.raises(ParameterError):
        _ = build(root)
    assert source.read_bytes() == original


def test_real_power_sections_figures_and_toc_render(power_publication: Path) -> None:
    pdf = build(power_publication)
    receipt = json.loads(
        (power_publication / "output/provenance/manuscript-template.json").read_text()
    )
    assert receipt["pdf_sha256"] == file_sha256(pdf)
    assert receipt["staged_figure_sha256"]["rejection-rates.png"] == file_sha256(
        power_publication / "output/power/figures/rejection-rates.png"
    )
    assert receipt["staged_figure_sha256"]["availability-calibration.png"] == file_sha256(
        power_publication / "output/power/figures/availability-calibration.png"
    )
    tex = (power_publication / "output/manuscript/rendered.tex").read_text()
    toc = (power_publication / "output/manuscript/rendered.toc").read_text()
    assert "\\label{sec:power}" in tex
    assert "\\label{eq:power-denominators}" in tex
    assert "Inference and prospective operating characteristics" in toc
    text = " ".join(" ".join(page.extract_text().split()) for page in PdfReader(pdf).pages)
    assert "Missing bounds" in text
    assert "undefined" in text
    assert "{{" not in text
    assert "[?]" not in text
