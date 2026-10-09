# Copyright (c) 2026 Daniel Ari Friedman
"""Display measured values with explicit conditioning, units and degeneracy."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import assert_never

from scripts.manuscript_data import ComplexityReport, PublicationData

type Variables = dict[str, str]


def number(value: float | None, digits: int) -> str:
    """Format display precision while preserving null means as absent values."""
    match value:
        case None:
            return "-"
        case int():
            return str(value)
        case float():
            return format(value, f".{digits}g")
        case unreachable:
            assert_never(unreachable)


def markdown_table(
    headers: tuple[str, ...], rows: list[tuple[str, ...]], *, right_align: tuple[int, ...] = ()
) -> str:
    """Emit a complete Pandoc table with stable column coverage."""
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|"
            + "|".join("---:" if index in right_align else "---" for index in range(len(headers)))
            + "|",
            *("| " + " | ".join(row) + " |" for row in rows),
        ]
    )


def measured_tables(data: PublicationData, digits: int, labels: Mapping[str, str]) -> Variables:
    """Use producer values and all status counts, never zero-fill nonfinite estimates."""
    baseline_rows = [
        (
            row.shape,
            row.structure,
            number(row.tolerance, digits),
            number(row.value, digits),
            row.status,
        )
        for row in data.baseline
        if row.measure == "hdse"
    ]
    result = {
        "BASELINE_TABLE": markdown_table(
            ("Shape", "Field", "$r$", "HDSE (nats)", "Status"), baseline_rows
        )
    }
    for name, family in (("MIX_TABLE", "mix"), ("CONTROL_TABLE", None)):
        selected = [
            row
            for row in data.summaries
            if row.geometry == "native"
            and row.measure == "hdse"
            and ((row.family == family) if family is not None else row.family != "mix")
        ]
        rows = [
            (
                row.shape,
                number(row.mixing, digits) if family else row.family,
                number(row.radius, digits),
                number(row.finite_mean, digits),
                number(row.finite_sample_sd, digits),
                f"{row.n_finite}/{row.n_total}",
                f"{row.n_undefined}/{row.n_infinite}",
            )
            for row in selected
        ]
        result[name] = (
            markdown_table(
                ("Shape", "$p$" if family else "Control", "$r$", "Mean", "SD", "Finite/n", "U/I"),
                rows,
            )
            if rows
            else "This component is disabled by the publication profile; no result is asserted."
        )
    other = [
        row
        for row in data.summaries
        if row.family == "mix" and row.geometry in {"native", "symbols"} and row.measure != "hdse"
    ]
    result["RELATED_RESULTS_TABLE"] = (
        markdown_table(
            ("Shape", "$p$", "Estimator", "Finite mean", "SD", "Finite/n", "U/I"),
            [
                (
                    row.shape,
                    number(row.mixing, digits),
                    labels.get(row.measure, row.measure.replace("_", " ")),
                    number(row.finite_mean, digits),
                    number(row.finite_sample_sd, digits),
                    f"{row.n_finite}/{row.n_total}",
                    f"{row.n_undefined}/{row.n_infinite}",
                )
                for row in other
            ],
        )
        if other
        else "No replicated related-estimator measurements are enabled in this profile."
    )
    counts = Counter(row.status for row in data.baseline)
    result.update(
        {
            "BASELINE_ROWS": str(len(data.baseline)),
            **{
                f"BASELINE_{status.upper()}": str(counts[status])
                for status in ("finite", "undefined", "infinite")
            },
        }
    )
    study_counts = Counter(row.status for row in data.study_rows)
    result.update(
        {
            "STUDY_ROWS": str(len(data.study_rows)),
            **{
                f"STUDY_{status.upper()}": str(study_counts[status])
                for status in ("finite", "undefined", "infinite")
            },
        }
    )
    return result


def cost_tables(payload: ComplexityReport | None) -> str:
    """Display exact producer work counts, excluding process-memory interpretations."""
    if payload is None:
        return "Analytical cost output is disabled by this publication profile."
    rows: list[tuple[str, ...]] = []
    for record in payload.records:
        estimate = record.estimate
        rows.extend(
            (
                " x ".join(map(str, estimate.input_shape)),
                f"{stage.name.removeprefix('distance_').replace('_', ' ')} {record.geometry.replace('flattened', 'flat')}",
                str(stage.templates),
                str(stage.features),
                str(stage.candidate_pairs),
                str(stage.distance_component_visits),
                str(record.guard_peak_bytes),
            )
            for stage in estimate.stages
        )
    table = markdown_table(
        ("Input", "Stage", "$n$", "$q$", "Pairs", "Visits", "Guard (B)"),
        list(dict.fromkeys(rows)),
        right_align=(2, 3, 4, 5, 6),
    )
    legend = "Here flat denotes row-major flattened observations; maximum and histogram denote the distance passes."
    return (
        legend
        + "\n\n\\begingroup\\small\\setlength{\\tabcolsep}{8pt}\n\n"
        + table
        + "\n\n\\endgroup"
    )
