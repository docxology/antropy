# Copyright (c) 2026 Daniel Ari Friedman
"""Pointwise outer Monte Carlo intervals, availability and prespecified null calibration."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill
from typing import Final

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from antropy_hd.errors import ParameterError
from scripts.power_models import PowerReport, PowerSummary
from scripts.study_plots import save_figure

PALETTE: Final[tuple[str, ...]] = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00")


def _defined(value: float | None) -> float:
    if value is None:
        raise ParameterError("interval", "An all-attempt or availability interval is missing")
    return value


def _interval_curve(axis: Axes, rows: list[PowerSummary], color: str, label: str) -> None:
    sizes = [item.sample_size for item in rows]
    rates = [_defined(item.unconditional_rejection.estimate) for item in rows]
    lower = [_defined(item.unconditional_rejection.lower) for item in rows]
    upper = [_defined(item.unconditional_rejection.upper) for item in rows]
    _ = axis.plot(sizes, rates, "o-", color=color, label=label, markersize=3, linewidth=1.2)
    _ = axis.fill_between(sizes, lower, upper, color=color, alpha=0.13)
    conditional = [
        item.conditional_rejection.estimate
        if item.conditional_rejection.estimate is not None
        else np.nan
        for item in rows
    ]
    _ = axis.plot(sizes, conditional, ":", color=color, linewidth=1)


def rejection_rates(report: PowerReport, path: Path) -> None:
    """Plot all declared scenarios; dotted conditional rates expose failure selection."""
    plan = report.plan
    figure, axes = plt.subplots(
        len(plan.analyses),
        len(plan.shapes),
        figsize=(2.5 * len(plan.shapes), 2.25 * len(plan.analyses)),
        squeeze=False,
    )
    for row, analysis in enumerate(plan.analyses):
        for col, shape in enumerate(plan.shapes):
            axis = axes[row, col]
            for index, scenario in enumerate(plan.scenarios):
                selected = sorted(
                    (
                        item
                        for item in report.summaries
                        if item.shape == shape
                        and item.analysis_id == analysis.spec.id
                        and item.scenario_id == scenario.id
                    ),
                    key=lambda item: item.sample_size,
                )
                _interval_curve(
                    axis,
                    selected,
                    PALETTE[index % len(PALETTE)],
                    f"p={scenario.first_probability:g} vs {scenario.second_probability:g}",
                )
            _ = axis.axhline(plan.target_power, color="#555555", linestyle="--", linewidth=0.8)
            _ = axis.axhline(plan.alpha, color="#777777", linestyle="-.", linewidth=0.8)
            _ = axis.set(
                ylim=(-0.03, 1.03),
            )
            _ = axis.set_title(
                fill(analysis.label, 22) + f"\n{len(shape)}D: {'x'.join(map(str, shape))}",
                fontsize=9,
            )
            _ = axis.set_xlabel("Independent fields per group", fontsize=8)
            _ = axis.set_ylabel("Rejection probability", fontsize=8)
            axis.tick_params(labelsize=8)
            axis.set_xticks(sorted(plan.sample_sizes))
            axis.grid(alpha=0.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    _ = figure.legend(
        handles, labels, loc="lower center", ncol=len(plan.scenarios), frameon=False, fontsize=8
    )
    title = f"{plan.multiplicity.title()} family; {plan.confidence_level:.0%} pointwise Wilson intervals"
    _ = figure.suptitle(title + "\nSolid: all attempts; dotted: available comparisons", fontsize=11)
    figure.tight_layout(rect=(0, 0.035, 1, 0.965))
    save_figure(figure, path)


def availability_calibration(report: PowerReport, path: Path) -> None:
    """Show stochastic null availability and raw versus fixed-family null rejection."""
    plan = report.plan
    nulls = [scenario for scenario in plan.scenarios if scenario.role == "null"]
    null_ids = {scenario.id for scenario in nulls}
    upper_limit = min(
        1.0,
        1.15
        * max(
            [plan.alpha]
            + [
                _defined(row.unconditional_rejection.upper)
                for row in report.summaries
                if row.scenario_id in null_ids
            ]
            + [
                row.raw_rejected / row.attempted
                for row in report.summaries
                if row.scenario_id in null_ids
            ]
        ),
    )
    columns = [(scenario, shape) for scenario in nulls for shape in plan.shapes]
    figure, axes = plt.subplots(2, len(columns), figsize=(2.6 * len(columns), 5.7), squeeze=False)
    for col, (scenario, shape) in enumerate(columns):
        for index, analysis in enumerate(plan.analyses):
            color = PALETTE[index % len(PALETTE)]
            rows = sorted(
                (
                    item
                    for item in report.summaries
                    if item.scenario_id == scenario.id
                    and item.shape == shape
                    and item.analysis_id == analysis.spec.id
                ),
                key=lambda item: item.sample_size,
            )
            sizes = [item.sample_size for item in rows]
            _ = axes[0, col].plot(
                sizes,
                [_defined(item.availability.estimate) for item in rows],
                "o-",
                color=color,
                label=analysis.label,
                markersize=3,
            )
            _ = axes[0, col].fill_between(
                sizes,
                [_defined(item.availability.lower) for item in rows],
                [_defined(item.availability.upper) for item in rows],
                color=color,
                alpha=0.1,
            )
            _interval_curve(axes[1, col], rows, color, analysis.label)
            _ = axes[1, col].plot(
                sizes,
                [item.raw_rejected / item.attempted for item in rows],
                "s--",
                color=color,
                markersize=3,
                fillstyle="none",
                linewidth=0.8,
            )
        for axis, ylabel in zip(
            axes[:, col], ("Available / attempted", "Null rejection / attempted"), strict=True
        ):
            _ = axis.set(
                ylim=(-0.03, 1.03),
            )
            _ = axis.set_title(
                fill(scenario.label, 22) + f"\n{len(shape)}D: {'x'.join(map(str, shape))}",
                fontsize=9,
            )
            _ = axis.set_xlabel("Independent fields per group", fontsize=8)
            _ = axis.set_ylabel(ylabel, fontsize=8)
            axis.tick_params(labelsize=8)
            axis.set_xticks(sorted(plan.sample_sizes))
            axis.grid(alpha=0.2)
        _ = axes[1, col].axhline(plan.alpha, color="#555555", linestyle="-.", linewidth=0.8)
        _ = axes[1, col].set_ylim(-0.03 * upper_limit, upper_limit)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    _ = figure.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=8)
    title = f"Stochastic null control; {plan.confidence_level:.0%} pointwise Wilson intervals"
    _ = figure.suptitle(
        title + f"\nBottom: solid {plan.multiplicity}; hollow squares unadjusted", fontsize=11
    )
    figure.tight_layout(rect=(0, 0.1, 1, 0.95))
    save_figure(figure, path)


def plot_power(report: PowerReport, directory: Path) -> None:
    """Create raster and vector figures directly from all validated scientific records."""
    rejection_rates(report, directory / "rejection-rates.png")
    availability_calibration(report, directory / "availability-calibration.png")
