# Copyright (c) 2026 Daniel Ari Friedman
"""Finite-estimate figures with explicit nonfinite status annotations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.run_experiments import ExperimentPlan, ExperimentRow


def plot_results(rows: list[ExperimentRow], path: Path, plan: ExperimentPlan) -> None:
    """Plot only finite estimates; explicitly annotate all nonfinite statuses."""
    figure, axes = plt.subplots(
        1, len(plan.shapes), figsize=(4 * len(plan.shapes), 4.6), squeeze=False
    )
    colors = {"periodic": "#245a81", "noise": "#c45824", "mixed": "#398259"}
    for axis, shape in zip(axes[0], plan.shapes, strict=True):
        for structure in plan.structures:
            selected = [
                row
                for row in rows
                if row["shape"] == "x".join(map(str, shape))
                and row["structure"] == structure
                and row["measure"] == "hdse"
            ]
            finite = [row for row in selected if row["status"] == "finite"]
            axis.plot(
                [row["tolerance"] for row in finite],
                [row["value"] for row in finite],
                "o-",
                color=colors[structure],
                label=structure,
            )
            statuses = [
                f"r={row['tolerance']}: {row['status']}"
                for row in selected
                if row["status"] != "finite"
            ]
            if statuses:
                axis.text(
                    0.02,
                    1.03 + 0.075 * (len(plan.structures) - 1 - plan.structures.index(structure)),
                    f"{structure}: " + "; ".join(statuses),
                    transform=axis.transAxes,
                    va="bottom",
                    fontsize=7,
                    color=colors[structure],
                    wrap=True,
                )
        axis.set(
            xlabel="Relative radius r (threshold = r SD)",
            ylabel="HDSE (nats)",
        )
        axis.set_title(f"{len(shape)}D ({' x '.join(map(str, shape))})", y=1.30)
        axis.set_xticks(plan.tolerances)
        span = max(plan.tolerances) - min(plan.tolerances)
        padding = 0.08 * span if span else 0.05 * max(plan.tolerances)
        axis.set_xlim(min(plan.tolerances) - padding, max(plan.tolerances) + padding)
        axis.grid(alpha=0.2)
    handles, labels = axes[0][0].get_legend_handles_labels()
    figure.legend(
        handles, labels, fontsize=9, loc="lower center", ncol=len(plan.structures), frameon=False
    )
    figure.tight_layout(rect=(0, 0.09, 1, 1))
    figure.savefig(
        path, dpi=180, metadata={"Software": "antropy-hd deterministic experiment pipeline"}
    )
    plt.close(figure)
