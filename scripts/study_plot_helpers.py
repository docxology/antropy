# Copyright (c) 2026 Daniel Ari Friedman
"""Draw trial summaries without fabricating variability for singleton finite groups."""

from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes

from scripts.study_models import StudySummary


@dataclass(frozen=True, slots=True)
class CurveAppearance:
    """Legend identity and a shared accessible color for one experimental curve."""

    color: str
    label: str


def draw_summary(axis: Axes, selected: list[StudySummary], appearance: CurveAppearance) -> None:
    """Break lines at absent means and draw error bars only where sample SD exists."""
    _ = axis.plot(
        [item.mixing for item in selected],
        [item.finite_mean if item.finite_mean is not None else np.nan for item in selected],
        marker="o",
        color=appearance.color,
        label=appearance.label,
    )
    replicated = [item for item in selected if item.finite_sample_sd is not None]
    if replicated:
        _ = axis.errorbar(
            [item.mixing for item in replicated],
            [item.finite_mean for item in replicated],
            yerr=[item.finite_sample_sd for item in replicated],
            fmt="none",
            capsize=3,
            color=appearance.color,
        )
    for item in selected:
        if item.n_finite == 1:
            _ = axis.annotate(
                "n=1",
                (item.mixing or 0.0, item.finite_mean or 0.0),
                xytext=(0, 6),
                textcoords="offset points",
                fontsize=7,
                ha="center",
                color=appearance.color,
            )
