# Copyright (c) 2026 Daniel Ari Friedman
"""Replicate variability, topology comparisons and uncensored outcome surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from scripts.study_models import StudyRow, StudySummary
from scripts.study_plot_helpers import CurveAppearance, draw_summary

PALETTE: Final[tuple[str, ...]] = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9")


def save_figure(figure: Figure, path: Path) -> None:
    """Write publication-scale PNG and vector PDF from the same figure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight", metadata={"Software": "antropy-hd"})
    figure.savefig(
        path.with_suffix(".pdf"),
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(figure)


def mix_curves(summary: list[StudySummary], path: Path) -> None:
    """Show finite-conditional means and sample SD over independent trials."""
    shapes = sorted({item.shape for item in summary}, key=lambda shape: (shape.count("x"), shape))
    radii = sorted({item.radius for item in summary if item.radius is not None})
    figure, axes = plt.subplots(1, len(shapes), figsize=(2.25 * len(shapes), 3.6), squeeze=False)
    for axis, shape in zip(axes[0], shapes, strict=True):
        for index, radius in enumerate(radii):
            selected = sorted(
                (
                    item
                    for item in summary
                    if item.shape == shape
                    and item.family == "mix"
                    and item.geometry == "native"
                    and item.radius == radius
                ),
                key=lambda item: item.mixing or 0.0,
            )
            draw_summary(
                axis, selected, CurveAppearance(PALETTE[index % len(PALETTE)], f"r={radius:g}")
            )
        axis.set(
            title=f"{shape.count('x') + 1}D: {shape}",
            xlabel="Replacement probability p",
            ylabel="HDSE (nats)",
        )
        axis.grid(alpha=0.2)
        axis.legend(fontsize=8, frameon=False)
    figure.suptitle("MIX: finite-conditional mean ± trial sample SD", fontsize=12)
    figure.tight_layout()
    save_figure(figure, path)


def degeneracy_grid(summary: list[StudySummary], path: Path) -> None:
    """Display all finite, undefined and infinite counts, including empty finite groups."""
    shapes = sorted({item.shape for item in summary}, key=lambda shape: (shape.count("x"), shape))
    radii = sorted({item.radius for item in summary if item.radius is not None})
    groups = sorted(
        {
            (item.family, item.mixing)
            for item in summary
            if item.geometry == "native" and item.radius is not None
        },
        key=lambda item: (item[0], item[1] or 0),
    )
    figure, axes = plt.subplots(
        1, len(shapes), figsize=(2.25 * len(shapes), 0.43 * len(groups) + 1.5), squeeze=False
    )
    for axis, shape in zip(axes[0], shapes, strict=True):
        selected = {
            (item.family, item.mixing, item.radius): item
            for item in summary
            if item.shape == shape and item.geometry == "native" and item.radius is not None
        }
        matrix = np.array(
            [
                [
                    selected[(*group, radius)].n_finite / selected[(*group, radius)].n_total
                    for radius in radii
                ]
                for group in groups
            ]
        )
        axis.imshow(matrix, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i, group in enumerate(groups):
            for j, radius in enumerate(radii):
                item = selected[(*group, radius)]
                axis.text(
                    j,
                    i,
                    f"{item.n_finite}/{item.n_undefined}/{item.n_infinite}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if matrix[i, j] > 0.65 else "black",
                )
        axis.set(title=f"{shape.count('x') + 1}D: {shape}", xlabel="Relative radius r")
        axis.set_xticks(range(len(radii)), [f"{r:g}" for r in radii])
        axis.set_yticks(
            range(len(groups)), [family if p is None else f"MIX p={p:g}" for family, p in groups]
        )
    figure.suptitle("Native HDSE: finite / undefined / infinite trial counts", fontsize=11)
    figure.tight_layout()
    save_figure(figure, path)


def topology_curves(summary: list[StudySummary], path: Path) -> None:
    """Compare native neighborhoods with explicitly row-major flattened SampEn."""
    shapes = sorted({item.shape for item in summary}, key=lambda shape: (shape.count("x"), shape))
    radii = sorted({item.radius for item in summary if item.radius is not None})
    radius = radii[len(radii) // 2]
    figure, axes = plt.subplots(1, len(shapes), figsize=(2.25 * len(shapes), 3.6), squeeze=False)
    for axis, shape in zip(axes[0], shapes, strict=True):
        for index, geometry in enumerate(("native", "flattened")):
            selected = sorted(
                (
                    item
                    for item in summary
                    if item.shape == shape
                    and item.family == "mix"
                    and item.geometry == geometry
                    and item.radius == radius
                ),
                key=lambda item: item.mixing or 0,
            )
            draw_summary(axis, selected, CurveAppearance(PALETTE[index], geometry))
        axis.set(
            title=f"{shape.count('x') + 1}D: {shape}",
            xlabel="Replacement probability p",
            ylabel="Entropy (nats)",
        )
        axis.grid(alpha=0.2)
        axis.legend(frameon=False, fontsize=8)
    figure.suptitle(f"Geometry changes template size and population (r={radius:g})", fontsize=12)
    figure.tight_layout()
    save_figure(figure, path)


def entropy_complexity(rows: list[StudyRow], path: Path) -> None:
    """Keep a shared full symbol alphabet when comparing entropy and disequilibrium."""
    shapes = sorted({row.shape for row in rows}, key=lambda shape: (shape.count("x"), shape))
    figure, axes = plt.subplots(1, len(shapes), figsize=(2.25 * len(shapes), 3.6), squeeze=False)
    symbols = {(row.case_id, row.analysis_id): row for row in rows if row.geometry == "symbols"}
    families = sorted({row.family for row in rows})
    for axis, shape in zip(axes[0], shapes, strict=True):
        for index, family in enumerate(families):
            pairs = [
                (row, symbols[(row.case_id, "statistical")])
                for row in rows
                if row.shape == shape
                and row.family == family
                and row.geometry == "symbols"
                and row.analysis_id == "shannon"
            ]
            axis.scatter(
                [h.value for h, _ in pairs],
                [c.value for _, c in pairs],
                color=PALETTE[index % len(PALETTE)],
                label=family,
                alpha=0.7,
                s=24,
            )
        axis.set(
            title=f"{shape.count('x') + 1}D: {shape}",
            xlabel="Normalized Shannon\nentropy H",
            ylabel="Statistical complexity C",
            xlim=(-0.02, 1.02),
        )
        axis.grid(alpha=0.2)
    handles, labels = axes[0][0].get_legend_handles_labels()
    figure.legend(
        handles, labels, loc="lower center", ncol=len(families), frameon=False, fontsize=8
    )
    figure.suptitle("Fixed-alphabet entropy-complexity plane; every trial shown", fontsize=12)
    figure.tight_layout(rect=(0, 0.10, 1, 1))
    save_figure(figure, path)


def plot_study(rows: list[StudyRow], summary: list[StudySummary], directory: Path) -> None:
    """Generate complementary views rather than ranking unlike entropy scales together."""
    directory.mkdir(parents=True, exist_ok=True)
    mix_curves(summary, directory / "mix-entropy.png")
    degeneracy_grid(summary, directory / "degeneracy.png")
    topology_curves(summary, directory / "native-v-flattened.png")
    entropy_complexity(rows, directory / "entropy-complexity.png")
