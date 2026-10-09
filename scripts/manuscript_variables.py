# Copyright (c) 2026 Daniel Ari Friedman
"""Generate all manuscript metrics and configured values from actual producer sources."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.rendering.manuscript_injection import substitute_manuscript_text

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import METHODS
from scripts.manuscript_data import PublicationData, file_sha256
from scripts.manuscript_profile import ManuscriptContext
from scripts.manuscript_tables import (
    Variables,
    cost_tables,
    markdown_table,
    measured_tables,
    number,
)
from scripts.manuscript_verification import verification_variables
from scripts.run_experiments import ExperimentPlan


def publication_variables(
    root: Path, context: ManuscriptContext, data: PublicationData
) -> Variables:
    """Bind title, design, measurements, work estimates and source identities to their inputs."""
    project, profile = context.project, context.profile
    digits = profile.numeric_digits
    snapshot = json.loads((root / "output/provenance/experiment-config.json").read_text())
    baseline = ExperimentPlan.model_validate(snapshot["plan"])
    values = {
        "PROJECT_TITLE": profile.title,
        "PROJECT_SUBTITLE": profile.subtitle,
        "PACKAGE_NAME": project.name,
        "PACKAGE_VERSION": project.version,
        "PROJECT_LICENSE": project.license,
        "REPOSITORY_URL": project.repository,
        "AUTHOR_NAMES": ", ".join(author.name for author in project.authors),
        "BUILD_DATE": profile.date,
        "METHOD_COUNT": str(len(METHODS)),
        "SOURCE_COVERAGE_FLOOR": number(project.coverage_floor, digits),
        "INFRA_COVERAGE_FLOOR": number(profile.infrastructure_coverage_floor, digits),
        "TEMPLATE_REPOSITORY": profile.template_repository,
        "TEMPLATE_REVISION": profile.template_revision,
        "TEMPLATE_EXEMPLAR": profile.template_exemplar,
        "BASELINE_SHAPES": ", ".join(" x ".join(map(str, shape)) for shape in baseline.shapes),
        "BASELINE_RADII": ", ".join(number(radius, digits) for radius in baseline.tolerances),
        "BASELINE_EMBEDDING": str(baseline.embedding_shape),
        "BASELINE_PERIOD": number(baseline.period, digits),
        "BASELINE_NOISE_AMPLITUDE": number(baseline.noise_amplitude, digits),
        "BASELINE_SEED": str(baseline.seed),
        "BASELINE_CSV_SHA256": file_sha256(root / "output/data/results.csv"),
        "COMPLEXITY_TABLE": cost_tables(data.complexity),
    }
    values.update(measured_tables(data, digits, profile.measure_labels))
    values["MEASURE_LABELS"] = "; ".join(
        f"{label}: {measure.replace('_', ' ')}" for measure, label in profile.measure_labels.items()
    )
    values.update(verification_variables(root, context))
    if data.study is None:
        values.update(
            dict.fromkeys(
                (
                    "STUDY_FIELDS",
                    "STUDY_SHAPES",
                    "STUDY_RADII",
                    "STUDY_REPLICATES",
                    "STUDY_PERIOD",
                    "STUDY_PHASE_ORIGIN",
                    "STUDY_MIXING",
                    "STUDY_EMBEDDING",
                    "STUDY_CONTROLS",
                    "STUDY_GAUSSIAN_SD",
                    "STUDY_CORRELATION_STEPS",
                    "STUDY_SYMBOL_BINS",
                    "STUDY_SYMBOL_RANGE",
                    "STUDY_SEED",
                    "STUDY_PLAN_TABLE",
                    "STUDY_REPORT_SHA256",
                    "STUDY_CSV_SHA256",
                ),
                "disabled by the publication profile",
            )
        )
    else:
        plan = data.study.plan
        values.update(
            {
                "STUDY_FIELDS": str(len(data.study.records)),
                "STUDY_SHAPES": ", ".join(" x ".join(map(str, shape)) for shape in plan.shapes),
                "STUDY_RADII": ", ".join(number(radius, digits) for radius in plan.radii),
                "STUDY_REPLICATES": str(plan.replicates),
                "STUDY_PERIOD": number(plan.period, digits),
                "STUDY_PHASE_ORIGIN": str(plan.phase_origin),
                "STUDY_MIXING": ", ".join(
                    number(probability, digits) for probability in plan.mixing_probabilities
                ),
                "STUDY_EMBEDDING": str(plan.embedding_shape),
                "STUDY_CONTROLS": ", ".join(plan.controls),
                "STUDY_GAUSSIAN_SD": number(plan.gaussian_sd, digits),
                "STUDY_CORRELATION_STEPS": str(plan.correlation_steps),
                "STUDY_SYMBOL_BINS": str(plan.symbol_bins),
                "STUDY_SYMBOL_RANGE": ", ".join(map(str, plan.symbol_range)),
                "STUDY_SEED": str(plan.seed),
                "STUDY_REPORT_SHA256": file_sha256(root / "output/study/report.json"),
                "STUDY_CSV_SHA256": file_sha256(root / "output/study/results.csv"),
                "STUDY_PLAN_TABLE": markdown_table(
                    ("Control", "Configured value"),
                    [
                        (key.replace("_", " "), json.dumps(value))
                        for key, value in plan.model_dump(mode="json").items()
                    ],
                ),
            }
        )
    if data.benchmark is None:
        values.update(
            BENCHMARK_NARRATIVE="Benchmark observations are disabled in this profile.",
            BENCHMARK_TABLE="No host timing is asserted.",
        )
    else:
        report = data.benchmark
        values["BENCHMARK_NARRATIVE"] = (
            f"The recorded environment is Python {report.python}, NumPy {report.numpy}, {report.platform}, machine {report.machine}. The configured plan uses {report.plan.warmups} warmups and {report.plan.repetitions} measured repetitions per request; block sizes are {', '.join(map(str, report.plan.block_sizes))}."
        )
        values["BENCHMARK_TABLE"] = markdown_table(
            ("Shape", "Block", "Median (s)", "Sample SD (s)", "Visits", "Guard (B)"),
            [
                (
                    " x ".join(map(str, row.shape)),
                    str(row.block_size),
                    number(row.median_seconds, digits),
                    number(row.sample_sd_seconds, digits),
                    str(row.estimate.distance_component_visits),
                    str(row.estimate.guard_peak_bytes),
                )
                for row in report.records
            ],
        )
    for figure in profile.figures:
        enabled = (
            figure.dependency == "baseline"
            or (figure.dependency == "study" and data.study is not None)
            or (figure.dependency == "benchmark" and data.benchmark is not None)
        )
        if not enabled:
            values[figure.token] = (
                "This figure is intentionally omitted by the explicit fixture/publication profile."
            )
            continue
        path = (root / figure.source).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ParameterError(
                "manuscript", f"Configured figure is missing or escaping: {figure.source}"
            )
        caption, unresolved = substitute_manuscript_text(figure.caption, values)
        if unresolved:
            raise ParameterError("manuscript", f"Unresolved figure caption values: {unresolved}")
        attributes = " width=100%" + (" fig-pos=p" if figure.float_page else "")
        values[figure.token] = (
            f"![{caption}](../../{figure.source}){{#fig:{figure.label}{attributes}}}"
        )
        if figure.float_page:
            values[figure.token] = "\\clearpage\n\n" + values[figure.token] + "\n\n\\clearpage"
    return values
