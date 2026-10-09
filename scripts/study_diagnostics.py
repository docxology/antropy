# Copyright (c) 2026 Daniel Ari Friedman
"""Show actual input neighborhoods and the counts underlying conditional entropy."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import ClassVar

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from antropy_hd.models import EntropyResult
from scripts.study_models import StudyReport
from scripts.study_plots import PALETTE, save_figure


class MatchEvidence(BaseModel):
    """Parse integer counts from the HDSE diagnostic boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore")
    base_matches: StrictInt = Field(ge=0)
    extended_matches: StrictInt = Field(ge=0)
    eligible_pairs: StrictInt = Field(ge=1)


def plot_inputs(report: StudyReport, directory: Path) -> None:
    """Show lines or central slices of stored fields, with a shared image color scale."""
    shapes = sorted(report.plan.shapes, key=lambda shape: (len(shape), shape))
    probabilities = sorted(report.plan.mixing_probabilities)
    probability = probabilities[len(probabilities) // 2]
    families = ["mix", *sorted(report.plan.controls)]
    records = {
        (record.case.shape, record.case.family): record
        for record in report.records
        if record.case.trial == 0
        and (record.case.mixing is None or record.case.mixing == probability)
    }
    arrays = {
        (shape, family): np.load(
            directory.parents[2] / records[(shape, family)].input_file, allow_pickle=False
        )
        for shape in shapes
        for family in families
    }
    low = min(float(array.min()) for array in arrays.values())
    high = max(float(array.max()) for array in arrays.values())
    figure, axes = plt.subplots(
        len(families), len(shapes), figsize=(2.25 * len(shapes), 1.3 * len(families)), squeeze=False
    )
    for i, shape in enumerate(shapes):
        for j, family in enumerate(families):
            array = arrays[(shape, family)]
            axis = axes[j, i]
            if array.ndim == 1:
                axis.plot(array, color=PALETTE[j % len(PALETTE)], linewidth=1)
                axis.set_ylim(low, high)
            else:
                while array.ndim > 2:
                    array = array[..., array.shape[-1] // 2]
                axis.imshow(
                    array, cmap="viridis", vmin=low, vmax=high, aspect="auto", origin="lower"
                )
            axis.set_title(f"{family}; {len(shape)}D {'x'.join(map(str, shape))}", fontsize=8)
            axis.tick_params(labelsize=6)
    figure.suptitle(
        f"Actual trial-0 inputs; MIX p={probability:g}; dimensions >2 use central slices",
        fontsize=12,
    )
    figure.tight_layout()
    save_figure(figure, directory / "input-fields.png")


def plot_match_probabilities(report: StudyReport, directory: Path) -> None:
    """Expose both marginal matching and extension survival, with missing ratios as gaps."""
    shapes = sorted(report.plan.shapes, key=lambda shape: (len(shape), shape))
    radii = sorted(report.plan.radii)
    radius = radii[len(radii) // 2]
    probability = sorted(report.plan.mixing_probabilities)
    figure, axes = plt.subplots(2, len(shapes), figsize=(2.25 * len(shapes), 6), squeeze=False)
    for column, shape in enumerate(shapes):
        base = []
        survival = []
        for p in probability:
            evidence = []
            for record in report.records:
                if (
                    record.case.shape == shape
                    and record.case.family == "mix"
                    and record.case.mixing == p
                ):
                    result = record.native.results[f"hdse-r{radius}"]
                    if isinstance(result, EntropyResult):
                        evidence.append(MatchEvidence.model_validate(result.diagnostics))
            base.append(
                statistics.mean(item.base_matches / item.eligible_pairs for item in evidence)
            )
            ratios = [
                item.extended_matches / item.base_matches for item in evidence if item.base_matches
            ]
            survival.append(statistics.mean(ratios) if ratios else np.nan)
        axes[0, column].plot(probability, base, "o-", color=PALETTE[column % len(PALETTE)])
        axes[1, column].plot(probability, survival, "o-", color=PALETTE[column % len(PALETTE)])
        axes[0, column].set(
            title=f"{len(shape)}D: {'x'.join(map(str, shape))}",
            ylabel="Mean B / eligible pairs",
            ylim=(-0.02, 1.02),
        )
        axes[1, column].set(
            xlabel="Replacement probability p",
            ylabel="Mean A / B conditional on B > 0",
            ylim=(-0.02, 1.02),
        )
        axes[0, column].grid(alpha=0.2)
        axes[1, column].grid(alpha=0.2)
    figure.suptitle(
        f"Matching evidence at r={radius:g}; trial means, not independent-pair probabilities",
        fontsize=12,
    )
    figure.tight_layout()
    save_figure(figure, directory / "match-probability.png")


def plot_diagnostics(report: StudyReport, root: Path) -> None:
    """Render evidence from stored fields and authenticated match counts."""
    directory = root / "output/study/figures"
    directory.mkdir(parents=True, exist_ok=True)
    plot_inputs(report, directory)
    plot_match_probabilities(report, directory)
