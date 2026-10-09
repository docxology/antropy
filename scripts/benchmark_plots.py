# Copyright (c) 2026 Daniel Ari Friedman
"""Separate exact scheduled work, guarded memory and empirical wall-clock timings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

from scripts.study_plots import PALETTE, save_figure

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.benchmark_models import BenchmarkReport


def plot_benchmark(report: BenchmarkReport, path: Path) -> None:
    """Use actual work inputs rather than treating different-dimensional cell counts as equal."""
    figure, axes = plt.subplots(1, 3, figsize=(6.75, 3.7))
    for dimension in sorted({len(record.shape) for record in report.records}):
        for block in sorted(report.plan.block_sizes):
            records = [
                record
                for record in report.records
                if len(record.shape) == dimension and record.block_size == block
            ]
            color = PALETTE[(dimension - 1) % len(PALETTE)]
            marker = "o" if block == min(report.plan.block_sizes) else "s"
            label = f"{dimension}D, block {block}"
            templates = [record.estimate.stages[0].templates for record in records]
            axes[0].plot(
                templates,
                [record.estimate.distance_component_visits for record in records],
                marker=marker,
                color=color,
                label=label,
            )
            axes[1].plot(
                templates,
                [record.estimate.guard_peak_bytes / 1024 for record in records],
                marker=marker,
                color=color,
                label=label,
            )
            axes[2].errorbar(
                [record.estimate.distance_component_visits for record in records],
                [record.median_seconds * 1000 for record in records],
                yerr=[record.sample_sd_seconds * 1000 for record in records],
                marker=marker,
                color=color,
                capsize=2,
                label=label,
            )
    axes[0].set(xlabel="Common-origin\ntemplates K", ylabel="Scheduled distance\ncomponent visits")
    axes[1].set(xlabel="Common-origin\ntemplates K", ylabel="Conservative guard\nworkspace (KiB)")
    axes[2].set(xlabel="Scheduled distance\ncomponent visits", ylabel="Observed median\ntime (ms)")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.grid(alpha=0.2)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=8)
    figure.suptitle(f"Real HDSE calls on {report.machine}; bars: repetition sample SD", fontsize=11)
    figure.tight_layout(rect=(0, 0.16, 1, 1))
    save_figure(figure, path)
