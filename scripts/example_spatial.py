# Copyright (c) 2026 Daniel Ari Friedman
"""Native-dimensional synthetic fields driven entirely by validated plans."""

from importlib.metadata import version

import numpy as np

from antropy_hd.orchestration import array_sha256
from antropy_hd.ordinal import weighted_permutation_entropy
from antropy_hd.spectral import svd_entropy
from antropy_hd.template_entropy import hdse
from scripts.example_models import SpatialPlan
from scripts.example_reports import SpatialCase, SpatialReport


def run_spatial(plan: SpatialPlan) -> SpatialReport:
    """Compute native field estimates after immutable-plan resource preflight."""
    cases: list[SpatialCase] = []
    for case in plan.cases:
        rng = np.random.default_rng(np.random.SeedSequence([plan.seed, *case.input_shape]))
        axes = np.indices(case.input_shape, dtype=np.float64)
        field = (
            plan.field.sine_amplitude * np.sin(axes[plan.field.sine_axis] / plan.field.sine_divisor)
            + plan.field.trend_slope * np.sum(axes, axis=0)
            + rng.normal(plan.field.mean, plan.field.standard_deviation, size=case.input_shape)
        )
        cases.append(
            SpatialCase(
                input_shape=case.input_shape,
                input_sha256=array_sha256(field),
                embedding=case.embedding,
                match=case.match,
                hdse=hdse(field, embedding=case.embedding, match=case.match),
                weighted_permutation=weighted_permutation_entropy(
                    field,
                    embedding=case.embedding,
                    base=plan.entropy_base,
                    normalize=plan.weighted_permutation_normalize,
                    max_pattern_length=plan.max_pattern_length,
                ),
                svd=svd_entropy(
                    field,
                    embedding=case.embedding,
                    base=plan.entropy_base,
                    demean=plan.svd_demean,
                    normalize=plan.svd_normalize,
                ),
            )
        )
    return SpatialReport(package_version=version("antropy-hd"), seed=plan.seed, cases=tuple(cases))
