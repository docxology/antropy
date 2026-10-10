# Copyright (c) 2026 Daniel Ari Friedman
"""Source-bound prospective inference tables, captions and resource descriptions."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.manuscript_data import file_sha256
from scripts.manuscript_power_tables import operating_tables
from scripts.manuscript_tables import Variables, markdown_table, number
from scripts.power_models import PowerReport


def resolution_restrictions(report: PowerReport, digits: int) -> str:
    """Derive the exact two-sided equal-group floor and fixed-family restriction."""
    plan = report.plan
    if str(plan.test.alternative) != "two_sided":
        return "Attainability depends on the configured tail alternative and allocation schedule."
    family = len(plan.analyses) if plan.multiplicity == "holm" else 1
    rows = [
        (
            str(item.sample_size),
            number(2 * item.resolution, digits),
            number(plan.alpha / family, digits),
            "precluded" if 2 * item.resolution > plan.alpha / family else "not precluded",
        )
        for item in report.resources.schedules
        if item.method == "exact"
    ]
    if not rows:
        return "The consumed schedule uses sampled allocations; exact-enumeration attainability is not asserted."
    threshold = (
        "The first Holm threshold is alpha divided by the declared family size"
        if plan.multiplicity == "holm"
        else "The unadjusted threshold is alpha"
    )
    return (
        "For equal-sized groups with exact two-sided enumeration, every allocation has a distinct complementary allocation with the same absolute contrast. The minimum attainable p-value is at least twice the exact grid increment. Ties can increase it. "
        + threshold
        + "; if even this lower bound exceeds that threshold, no family member can reject. This necessary-condition calculation does not guarantee rejection at other group sizes.\n\n"
        + markdown_table(
            ("$n$", "Two-sided p floor", "First threshold", "Rejection by floor"), rows
        )
    )


def power_variables(root: Path, report: PowerReport | None, digits: int) -> Variables:
    """Resolve power-only variables; an explicitly disabled fixture asserts no measured result."""
    if report is None:
        return {
            "POWER_NARRATIVE": "Prospective operating-characteristic analysis is disabled by this explicit publication profile; no power or null-calibration result is asserted.",
            "POWER_ABSTRACT": "Prospective operating-characteristic measurements are disabled in this explicit publication profile.",
            "POWER_REJECTION_TABLE": "No prospective measurements enabled.",
            "POWER_AVAILABILITY_TABLE": "No prospective measurements enabled.",
            "POWER_EFFECT_TABLE": "No prospective measurements enabled.",
        }
    plan = report.plan
    scenarios = "; ".join(
        f"{scenario.label} ({scenario.role}, p={number(scenario.first_probability, digits)} versus {number(scenario.second_probability, digits)})"
        for scenario in plan.scenarios
    )
    analyses = "\n\n".join(
        f"### {analysis.label}\n\nGeometry: {analysis.geometry}; registered measure: `{analysis.spec.measure}`. Explicit invocation parameters:\n\n```json\n{json.dumps(analysis.spec.parameters, indent=2, sort_keys=True)}\n```"
        for analysis in plan.analyses
    )
    values = {
        "POWER_ALPHA": number(plan.alpha, digits),
        "POWER_CONFIDENCE": number(plan.confidence_level, digits),
        "POWER_TARGET": number(plan.target_power, digits),
        "POWER_REPETITIONS": str(plan.repetitions),
        "POWER_SAMPLE_SIZES": ", ".join(map(str, plan.sample_sizes)),
        "POWER_ANALYSIS_COUNT": str(len(plan.analyses)),
        "POWER_MULTIPLICITY": plan.multiplicity,
        "POWER_SCENARIOS_CAPTION": scenarios,
        "POWER_NULL_SCENARIOS_CAPTION": "; ".join(
            f"{scenario.label} (p={number(scenario.first_probability, digits)} in both groups)"
            for scenario in plan.scenarios
            if scenario.role == "null"
        ),
        "POWER_SHAPES": ", ".join("x".join(map(str, shape)) for shape in plan.shapes),
        "POWER_ANALYSIS_LABELS": ", ".join(analysis.label for analysis in plan.analyses),
        "POWER_SEED": str(plan.seed),
        "POWER_PAIRING": str(plan.test.pairing),
        "POWER_ALTERNATIVE": str(plan.test.alternative),
        "POWER_MODE": str(plan.test.mode),
        "POWER_FIELDS": str(len(report.estimates)),
        "POWER_POOLS": str(len(report.pools)),
        "POWER_DECISIONS": str(len(report.experiments)),
        "POWER_SUMMARIES": str(len(report.summaries)),
        "POWER_UNAVAILABLE": str(
            sum(decision.status == "unavailable" for decision in report.experiments)
        ),
        "POWER_AVAILABLE": str(
            sum(decision.status == "available" for decision in report.experiments)
        ),
        "POWER_WORST_MC_SE": number(report.resources.worst_case_mc_standard_error, digits),
        "POWER_REPORT_SHA256": file_sha256(root / "output/power/report.json"),
        "POWER_PLAN_SHA256": report.plan_sha256,
        "POWER_ANALYSIS_DETAILS": analyses,
        "POWER_PLAN_TABLE": markdown_table(
            ("Control", "Configured value"),
            [
                (key.replace("_", " "), json.dumps(value))
                for key, value in plan.model_dump(mode="json").items()
                if key not in {"test", "analyses", "scenarios"}
            ],
        ),
        "POWER_TEST_TABLE": markdown_table(
            ("Inference control", "Configured value"),
            [
                (key.replace("_", " "), json.dumps(value))
                for key, value in plan.test.model_dump(mode="json").items()
            ],
        ),
        "POWER_SCENARIO_TABLE": markdown_table(
            ("Scenario", "Role", "First $p$", "Second $p$"),
            [
                (
                    scenario.label,
                    scenario.role,
                    number(scenario.first_probability, digits),
                    number(scenario.second_probability, digits),
                )
                for scenario in plan.scenarios
            ],
        ),
        "POWER_SCHEDULE_TABLE": markdown_table(
            ("$n$", "Allocations", "Evaluated", "Mode", "Work", "Grid increment"),
            [
                (
                    str(item.sample_size),
                    str(item.allocations),
                    str(item.evaluated),
                    item.method,
                    str(item.work),
                    number(item.resolution, digits),
                )
                for item in report.resources.schedules
            ],
        ),
        "POWER_RESOURCE_TABLE": markdown_table(
            ("Scheduled resource", "Count"),
            [
                ("Fields", str(report.resources.fields)),
                ("Decisions", str(report.resources.experiments)),
                ("Distance component visits", str(report.resources.distance_component_visits)),
                ("Inference scalar work", str(report.resources.inference_work)),
                ("Peak live pool arrays (bytes)", str(report.resources.peak_pool_bytes)),
            ],
        ),
    }
    values.update(operating_tables(report, digits))
    values["POWER_ABSTRACT"] = (
        f"A separate prospective simulation retains {values['POWER_FIELDS']} whole-field estimator records, {values['POWER_DECISIONS']} inference decisions and {values['POWER_SUMMARIES']} operating-characteristic cells. The configured procedure compares {values['POWER_ANALYSIS_COUNT']} estimators under {values['POWER_MULTIPLICITY']} multiplicity control at significance level {values['POWER_ALPHA']}, with pointwise {values['POWER_CONFIDENCE']} confidence intervals. Availability and selected rejection retain separate denominators; these synthetic operating characteristics do not certify a scientific sample size."
    )
    values["POWER_NARRATIVE"] = "\n\n".join(
        (
            f"The consumed design uses shapes {values['POWER_SHAPES']}, group sizes {values['POWER_SAMPLE_SIZES']} and {values['POWER_REPETITIONS']} independent outer repetitions per cell, with root seed {values['POWER_SEED']}. The comparison is {values['POWER_PAIRING']} and {values['POWER_ALTERNATIVE']}; the configured allocation mode is {values['POWER_MODE']}. The significance threshold is {values['POWER_ALPHA']}, interval confidence level {values['POWER_CONFIDENCE']} and configured planning target {values['POWER_TARGET']}. Multiplicity policy: {values['POWER_MULTIPLICITY']}. The declared estimators are {values['POWER_ANALYSIS_LABELS']}.",
            values["POWER_SCENARIO_TABLE"],
            values["POWER_PLAN_TABLE"],
            values["POWER_TEST_TABLE"],
            values["POWER_ANALYSIS_DETAILS"],
            f"The report retains {values['POWER_POOLS']} stored pools, {values['POWER_FIELDS']} whole-field estimator records and {values['POWER_DECISIONS']} inference decisions: {values['POWER_AVAILABLE']} available and {values['POWER_UNAVAILABLE']} unavailable. It emits {values['POWER_SUMMARIES']} operating-characteristic cells. The preflight worst-case binomial Monte Carlo standard-error bound is {values['POWER_WORST_MC_SE']}; it is a simulation-precision bound, not a statement of scientific effect precision.",
            values["POWER_SCHEDULE_TABLE"],
            resolution_restrictions(report, digits),
            values["POWER_RESOURCE_TABLE"],
            "\\begingroup\\small\n\n```text\nPower plan:   "
            + values["POWER_PLAN_SHA256"]
            + "\nPower report: "
            + values["POWER_REPORT_SHA256"]
            + "\n```\n\n\\endgroup",
        )
    )
    return values
