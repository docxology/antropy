# Copyright (c) 2026 Daniel Ari Friedman
"""Replicate inference with actual allocation counts, intervals and family adjustment."""

from importlib.metadata import version

from antropy_hd.inference import (
    binomial_interval,
    bootstrap_interval,
    holm_adjust,
    permutation_test,
)
from scripts.example_models import InferencePlan
from scripts.example_reports import InferenceReport


def run_inference(plan: InferencePlan) -> InferenceReport:
    """Compute every reported p-value and interval from explicitly declared controls."""
    permutation = permutation_test(plan.first, plan.second, config=plan.permutation)
    family = (permutation.p_value, *plan.additional_p_values)
    return InferenceReport(
        package_version=version("antropy-hd"),
        plan=plan,
        permutation=permutation,
        bootstrap=bootstrap_interval(plan.first, plan.second, config=plan.bootstrap),
        binomial=binomial_interval(
            plan.binomial.successes,
            plan.binomial.total,
            confidence_level=plan.binomial.confidence_level,
        ),
        family_p_values=family,
        holm_adjusted=holm_adjust(family),
    )
