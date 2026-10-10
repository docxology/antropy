# Copyright (c) 2026 Daniel Ari Friedman
"""Complete operating-characteristic tables with producer-authored denominators."""

from __future__ import annotations

from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import IntervalResult
from scripts.manuscript_tables import Variables, markdown_table, number
from scripts.power_models import PowerReport


def effect_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    """Allocate numeric columns enough width to preserve visible separation of full values."""
    weights = (10, 5, 25, 20, 20, 10, 10)
    if len(headers) != len(weights) or any(len(row) != len(headers) for row in rows):
        raise ParameterError("table", "Effect table rows must cover every declared column")
    numeric = {1, 3, 4, 5, 6}
    separator = (
        "|"
        + "|".join(
            "-" * width + (":" if index in numeric else "") for index, width in enumerate(weights)
        )
        + "|"
    )
    lines = [
        "| " + " | ".join(headers) + " |",
        separator,
        *("| " + " | ".join(row) + " |" for row in rows),
    ]
    return (
        "\\begingroup\\small\\setlength{\\tabcolsep}{8pt}\n\n" + "\n".join(lines) + "\n\n\\endgroup"
    )


def interval_text(result: IntervalResult, digits: int) -> str:
    """Preserve undefined intervals and display the producer's pointwise bounds."""
    if result.estimate is None:
        return str(result.status)
    return f"{number(result.estimate, digits)} [{number(result.lower, digits)}, {number(result.upper, digits)}]"


def operating_tables(report: PowerReport, digits: int) -> Variables:
    """Retain every scenario, shape, group size, method and missing-decision denominator."""
    labels = {analysis.spec.id: analysis.label for analysis in report.plan.analyses}
    rejection: list[str] = []
    availability: list[str] = []
    effects: list[str] = []
    for scenario in report.plan.scenarios:
        rows = [row for row in report.summaries if row.scenario_id == scenario.id]
        heading = f"### {scenario.label}\n\n"
        rejection.append(
            heading
            + markdown_table(
                ("Shape", "$n$", "Method", "Available/R", "Rejects/R", "Unconditional [CI]"),
                [
                    (
                        "x".join(map(str, row.shape)),
                        str(row.sample_size),
                        labels[row.analysis_id],
                        f"{row.available}/{row.attempted}",
                        f"{row.rejected}/{row.attempted}",
                        interval_text(row.unconditional_rejection, digits),
                    )
                    for row in rows
                ],
            )
        )
        availability.append(
            heading
            + markdown_table(
                (
                    "Shape",
                    "$n$",
                    "Method",
                    "Availability [CI]",
                    "Conditional [CI]",
                    "Missing bounds",
                ),
                [
                    (
                        "x".join(map(str, row.shape)),
                        str(row.sample_size),
                        labels[row.analysis_id],
                        interval_text(row.availability, digits),
                        interval_text(row.conditional_rejection, digits),
                        f"[{number(row.missing_decision_lower, digits)}, {number(row.missing_decision_upper, digits)}]",
                    )
                    for row in rows
                ],
            )
        )
        effects.append(
            heading
            + effect_table(
                (
                    "Shape",
                    "$n$",
                    "Method",
                    "Mean $\\Delta$",
                    "SD",
                    "Raw",
                    "Adj.",
                ),
                [
                    (
                        "x".join(map(str, row.shape)),
                        str(row.sample_size),
                        labels[row.analysis_id],
                        number(row.mean_difference_mean, digits),
                        number(row.mean_difference_sd, digits),
                        str(row.raw_rejected),
                        str(row.rejected),
                    )
                    for row in rows
                ],
            )
        )
    return {
        "POWER_REJECTION_TABLE": "\n\n".join(rejection),
        "POWER_AVAILABILITY_TABLE": "\n\n".join(availability),
        "POWER_EFFECT_TABLE": "\n\n".join(effects),
    }
