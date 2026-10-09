# Copyright (c) 2026 Daniel Ari Friedman
"""Real-file and native-render controls for configured manuscript production."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from pypdf import PdfReader

from antropy_hd.errors import ParameterError
from scripts.benchmark_complexity import benchmark
from scripts.build_manuscript import build, manuscript_source
from scripts.manuscript_data import file_sha256, json_source, read_data
from scripts.manuscript_hydration import hydrate, section_texts
from scripts.manuscript_profile import load_context
from scripts.manuscript_variables import publication_variables, verification_variables
from scripts.render_manuscript import (
    render_pdf,
    validate_images,
    validate_latex_output,
)
from scripts.template_provenance import template_identity
from tests.artifact_fixtures import REPOSITORY
from tests.artifact_fixtures import artifacts as artifacts  # noqa: PLC0414
from tests.artifact_fixtures import baseline as baseline  # noqa: PLC0414
from tests.test_manuscript_verification import write_verification
from tests.test_study_artifacts import small_study as small_study  # noqa: PLC0414


@pytest.fixture
def publication(artifacts: Path, small_study: Path) -> Path:
    shutil.copytree(small_study / "output/study", artifacts / "output/study")
    shutil.copyfile(small_study / "study_plan.yaml", artifacts / "study_plan.yaml")
    plan = yaml.safe_load((REPOSITORY / "benchmark_plan.yaml").read_text())
    plan.update(shapes=[[10]], block_sizes=[4], repetitions=2, warmups=0)
    path = artifacts / "benchmark_plan.yaml"
    path.write_text(yaml.safe_dump(plan))
    _ = benchmark(artifacts, path)
    rewrite_profile(
        artifacts, {"study_required": True, "complexity_required": True, "benchmark_required": True}
    )
    return artifacts


def rewrite_profile(root: Path, changes: dict) -> None:
    path = root / "docs/manuscript/project.yaml"
    profile = yaml.safe_load(path.read_text())
    profile.update(changes)
    path.write_text(yaml.safe_dump(profile))


def test_native_pdf_has_ordered_toc_math_and_resolved_bibliography(baseline: Path) -> None:
    reader = PdfReader(baseline / "output/pdf/antropy-methods.pdf")
    receipt = json.loads((baseline / "output/provenance/manuscript-template.json").read_text())
    tex = (baseline / "work/manuscript-build/pdf/_combined_manuscript.tex").read_text()
    toc = (baseline / "work/manuscript-build/pdf/_combined_manuscript.toc").read_text()
    context = load_context(baseline)
    assert receipt["section_order"] == list(context.profile.sections)
    assert receipt["pdf_pages"] == len(reader.pages) >= 3
    assert receipt["pdf_sha256"] == file_sha256(baseline / "output/pdf/antropy-methods.pdf")
    assert "\\tableofcontents" in tex
    assert "\\contentsline" in toc
    assert "\\label{eq:hdse}" in tex
    assert "\\bibliography{references}" in tex
    assert reader.outline
    assert "[?]" not in "\n".join(page.extract_text() for page in reader.pages)


def test_profile_and_project_values_flow_into_resolved_variables(artifacts: Path) -> None:
    rewrite_profile(artifacts, {"title": "Configured title 271", "numeric_digits": 4})
    context = load_context(artifacts)
    variables = publication_variables(artifacts, context, read_data(artifacts, context))
    _ = hydrate(artifacts, context, variables)
    persisted = json.loads((artifacts / "output/data/manuscript_variables.json").read_text())
    config = yaml.safe_load((artifacts / "output/manuscript/config.yaml").read_text())
    assert config["paper"]["title"] == "Configured title 271"
    assert config["paper"]["version"] == context.project.version
    assert persisted["BASELINE_ROWS"] == "30"
    assert persisted["BASELINE_SHAPES"] == "12, 5 x 5"
    assert persisted["STUDY_ROWS"] == "0"
    assert "{{" not in manuscript_source(artifacts)


@pytest.mark.parametrize("option", ["study_required", "complexity_required", "benchmark_required"])
def test_required_producer_is_not_silently_omitted(artifacts: Path, option: str) -> None:
    rewrite_profile(artifacts, {option: True})
    with pytest.raises(ParameterError):
        read_data(artifacts, load_context(artifacts))


@pytest.mark.parametrize(
    "changes",
    [
        {"sections": ["../escape.md"]},
        {"sections": ["00_abstract.md", "00_abstract.md"]},
        {"affiliations": {"Undeclared": "Institute"}},
        {"unconsumed": True},
    ],
)
def test_invalid_profile_is_rejected(artifacts: Path, changes: dict) -> None:
    rewrite_profile(artifacts, changes)
    with pytest.raises((ParameterError, ValidationError)):
        load_context(artifacts)


def test_unknown_token_fails_before_resolved_tree_changes(artifacts: Path) -> None:
    context = load_context(artifacts)
    variables = publication_variables(artifacts, context, read_data(artifacts, context))
    original = (artifacts / "output/manuscript/00_abstract.md").read_bytes()
    source = artifacts / "docs/manuscript/00_abstract.md"
    source.write_text(source.read_text() + "\n{{UNDECLARED_VARIABLE}}\n")
    with pytest.raises(ParameterError):
        hydrate(artifacts, context, variables)
    assert (artifacts / "output/manuscript/00_abstract.md").read_bytes() == original


def test_missing_auxiliary_and_figure_fail(artifacts: Path) -> None:
    context = load_context(artifacts)
    variables = publication_variables(artifacts, context, read_data(artifacts, context))
    (artifacts / "docs/manuscript/references.bib").unlink()
    with pytest.raises(ParameterError):
        hydrate(artifacts, context, variables)
    with pytest.raises(ParameterError):
        validate_images(artifacts, "![missing](../../output/figures/missing.png)")


def test_false_template_revision_is_rejected(baseline: Path) -> None:
    context = load_context(baseline)
    profile = context.profile.model_copy(update={"template_revision": "0" * 40})
    with pytest.raises(ParameterError):
        template_identity(context.model_copy(update={"profile": profile}))


def test_template_sources_and_tools_are_authenticated(baseline: Path) -> None:
    identity = template_identity(load_context(baseline))
    assert identity.installed_source_sha256["infrastructure/rendering/pdf_renderer.py"]
    assert set(identity.tools) == {"pandoc", "pandoc-crossref", "xelatex", "bibtex"}


@pytest.mark.parametrize(
    "diagnostic",
    [
        "! Undefined control sequence.",
        "Missing character: x",
        "There were undefined references",
        "Citation `absent' undefined",
        "LaTeX Warning: There were multiply-defined labels.",
    ],
)
def test_latex_written_pdf_does_not_mask_diagnostic_failure(
    tmp_path: Path, diagnostic: str
) -> None:
    log = tmp_path / "compile.log"
    log.write_text(diagnostic)
    with pytest.raises(ParameterError):
        validate_latex_output(log)


def test_missing_latex_log_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ParameterError):
        validate_latex_output(tmp_path / "absent.log")


def test_real_latex_error_is_fatal_even_when_upstream_writes_pdf(artifacts: Path) -> None:
    preamble = artifacts / "docs/manuscript/preamble.md"
    preamble.write_text(
        preamble.read_text().replace("\\setcounter{tocdepth}{2}", "\\antropyUndefinedCommand")
    )
    with pytest.raises(ParameterError):
        build(artifacts)
    log = artifacts / "work/manuscript-build/pdf/_combined_manuscript.log"
    assert "! Undefined control sequence." in log.read_text()


def test_conflicting_figure_basenames_are_rejected(artifacts: Path) -> None:
    alternate = artifacts / "output/alternate"
    alternate.mkdir()
    (alternate / "hdse-tolerance.png").write_bytes(b"different figure")
    source = (
        manuscript_source(artifacts) + "\n![duplicate](../../output/alternate/hdse-tolerance.png)\n"
    )
    with pytest.raises(ParameterError):
        render_pdf(artifacts, source, artifacts / "output/pdf/rejected.pdf")


def test_nonfinite_json_and_missing_required_sources_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text('{"value":NaN}')
    with pytest.raises(ValueError, match="Out of range"):
        json_source(path, required=True)
    with pytest.raises(ParameterError):
        json_source(tmp_path / "missing.json", required=True)


def test_verification_receipts_require_real_passing_run(artifacts: Path) -> None:
    context = load_context(artifacts)
    directory = write_verification(artifacts)
    prefix = context.profile.verification_prefix
    (directory / f"source-tests-{prefix}.log").write_text("3 failed")
    with pytest.raises(ParameterError):
        verification_variables(artifacts, context)
    (directory / f"source-tests-{prefix}.log").write_text("3 passed")
    variables = verification_variables(artifacts, context)
    assert (
        file_sha256(directory / f"source-tests-{prefix}.log") in variables["VERIFICATION_NARRATIVE"]
    )


def test_section_order_reconfiguration_controls_hydration(artifacts: Path) -> None:
    context = load_context(artifacts)
    selected = tuple(reversed(context.profile.sections))
    rewrite_profile(artifacts, {"sections": list(selected)})
    changed = load_context(artifacts)
    variables = publication_variables(artifacts, changed, read_data(artifacts, changed))
    texts = section_texts(artifacts, changed, variables)
    assert texts[0].startswith(
        (artifacts / "docs/manuscript" / selected[0]).read_text().splitlines()[0]
    )


def test_replicated_and_cost_variables_come_from_real_producers(publication: Path) -> None:
    context = load_context(publication)
    data = read_data(publication, context)
    variables = publication_variables(publication, context, data)
    assert variables["STUDY_FIELDS"] == "16"
    assert variables["STUDY_ROWS"] == "144"
    assert variables["STUDY_REPLICATES"] == "2"
    assert variables["STUDY_RADII"] == "1.5, 2"
    assert variables["STUDY_PHASE_ORIGIN"] == "1"
    assert data.benchmark is not None
    assert len(data.benchmark.records) == 1
    assert variables["STUDY_CSV_SHA256"] == file_sha256(publication / "output/study/results.csv")
    assert "{{" not in "\n".join(section_texts(publication, context, variables))


def test_full_profile_renders_authenticated_producer_figures(publication: Path) -> None:
    pdf = build(publication)
    receipt = json.loads((publication / "output/provenance/manuscript-template.json").read_text())
    context = load_context(publication)
    expected = {
        Path(figure.source).name: file_sha256(publication / figure.source)
        for figure in context.profile.figures
    }
    assert receipt["staged_figure_sha256"] == expected
    assert receipt["pdf_sha256"] == file_sha256(pdf)
    assert (publication / "output/manuscript/rendered.toc").is_file()


def test_publication_claims_include_all_configured_producer_bindings(publication: Path) -> None:
    from scripts.manuscript_claims import write_claims

    context = load_context(publication)
    write_claims(publication, read_data(publication, context))
    claims = json.loads((publication / "docs/manuscript/claims.json").read_text())
    assert {item["id"] for item in claims["claims"]} == {
        "hdse-contract",
        "related-contracts",
        "synthetic-estimates",
        "synthetic-design",
        "study-estimates",
        "study-design",
        "complexity-plan",
        "measured-runtime",
        "template-renderer",
    }


def test_stale_study_cannot_be_published(publication: Path) -> None:
    path = publication / "output/study/summary.json"
    payload = json.loads(path.read_text())
    selected = next(row for row in payload if row["finite_mean"] is not None)
    selected["finite_mean"] += 0.1
    path.write_text(json.dumps(payload))
    previous = (publication / "output/pdf/antropy-methods.pdf").read_bytes()
    with pytest.raises(ParameterError):
        build(publication)
    assert (publication / "output/pdf/antropy-methods.pdf").read_bytes() == previous


@pytest.mark.parametrize("change", ["duplicate_label", "escaping_figure"])
def test_figure_profile_invalid_identity_is_rejected(artifacts: Path, change: str) -> None:
    path = artifacts / "docs/manuscript/project.yaml"
    profile = yaml.safe_load(path.read_text())
    if change == "duplicate_label":
        profile["figures"][1]["label"] = profile["figures"][0]["label"]
    else:
        profile["figures"][0]["source"] = "../escape.png"
    path.write_text(yaml.safe_dump(profile))
    with pytest.raises(ParameterError):
        load_context(artifacts)
