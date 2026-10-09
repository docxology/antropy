# Copyright (c) 2026 Daniel Ari Friedman
"""Independent construction, topology and trial-aggregation controls."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import JsonValue, ValidationError

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import AnalysisSpec, analyze
from scripts.study_analysis import summarize
from scripts.study_fields import study_cases, study_field, symbol_probabilities
from scripts.study_models import StudyCase, StudyPlan, StudyRow


@pytest.fixture
def study_plan() -> StudyPlan:
    path = Path(__file__).resolve().parents[1] / "study_plan.yaml"
    return StudyPlan.model_validate(yaml.safe_load(path.read_text()))


def test_mix_zero_is_exact_unscaled_axis_sine_sum(study_plan: StudyPlan) -> None:
    case = StudyCase(shape=(5, 6), family="mix", mixing=0.0, trial=0)
    expected = np.array(
        [
            [
                math.sin(2 * math.pi * (i + study_plan.phase_origin) / study_plan.period)
                + math.sin(2 * math.pi * (j + study_plan.phase_origin) / study_plan.period)
                for j in range(6)
            ]
            for i in range(5)
        ]
    )
    np.testing.assert_allclose(
        study_field(study_plan, case), expected, rtol=0, atol=8 * np.finfo(float).eps
    )


def test_mix_one_uses_bounded_uniform_replacement(study_plan: StudyPlan) -> None:
    case = StudyCase(shape=(1000,), family="mix", mixing=1.0, trial=0)
    field = study_field(study_plan, case)
    assert np.all(np.abs(field) <= math.sqrt(3))
    assert abs(float(np.mean(field))) < 0.1
    assert abs(float(np.var(field)) - 1) < 0.1


def test_common_random_numbers_are_nested_across_mix_probabilities(study_plan: StudyPlan) -> None:
    cases = [StudyCase(shape=(100,), family="mix", mixing=p, trial=0) for p in (0, 0.25, 0.75, 1)]
    baseline, low, high, replacement = [study_field(study_plan, case) for case in cases]
    changed_low = low != baseline
    changed_high = high != baseline
    assert np.all(changed_low <= changed_high)
    np.testing.assert_array_equal(low[changed_low], replacement[changed_low])
    np.testing.assert_array_equal(high[changed_high], replacement[changed_high])


def test_reordering_design_axes_does_not_change_case_or_seed(study_plan: StudyPlan) -> None:
    reordered = study_plan.model_copy(
        update={
            "shapes": tuple(reversed(study_plan.shapes)),
            "controls": tuple(reversed(study_plan.controls)),
            "mixing_probabilities": tuple(reversed(study_plan.mixing_probabilities)),
        }
    )
    assert study_cases(reordered) == study_cases(study_plan)
    case = StudyCase(shape=study_plan.shapes[-1], family="mix", mixing=0.5, trial=2)
    np.testing.assert_array_equal(study_field(reordered, case), study_field(study_plan, case))


@pytest.mark.parametrize(
    "family", ["constant", "checkerboard", "gaussian", "correlated", "shuffled"]
)
def test_controls_preserve_native_shape_and_finite_values(
    study_plan: StudyPlan, family: str
) -> None:
    case = StudyCase.model_validate(
        {"shape": (5, 7, 6), "family": family, "mixing": None, "trial": 1}
    )
    field = study_field(study_plan, case)
    assert field.shape == case.shape
    assert np.isfinite(field).all()


def test_shuffling_preserves_histogram_but_changes_neighborhoods(study_plan: StudyPlan) -> None:
    original = study_field(study_plan, StudyCase(shape=(8, 9), family="mix", mixing=0, trial=0))
    shuffled = study_field(
        study_plan, StudyCase(shape=(8, 9), family="shuffled", mixing=None, trial=0)
    )
    np.testing.assert_array_equal(np.sort(original.ravel()), np.sort(shuffled.ravel()))
    assert not np.array_equal(original, shuffled)


def test_fixed_alphabet_retains_empty_and_overflow_symbols(study_plan: StudyPlan) -> None:
    probabilities = symbol_probabilities(np.array([-1000.0, 1000.0]), study_plan)
    assert len(probabilities) == study_plan.symbol_bins
    assert probabilities[0] == probabilities[-1] == 0.5
    assert np.count_nonzero(probabilities) == 2


def test_statistical_measure_is_orchestratable_with_typed_config() -> None:
    spec = AnalysisSpec(
        id="complexity",
        measure="statistical_complexity",
        parameters={"config": {"alphabet_size": 2}},
    )
    result = analyze([0.5, 0.5], spec)
    assert not isinstance(result, tuple)
    assert result.value == 0


def test_aggregation_keeps_degeneracy_and_uses_trial_sample_sd() -> None:
    rows = [
        StudyRow(
            case_id=f"trial{trial}",
            shape="8",
            dimension=1,
            family="mix",
            mixing=0.5,
            trial=trial,
            geometry="native",
            analysis_id="hdse",
            measure="hdse",
            radius=2,
            value=value,
            status=status,
            observations=6,
            parameters_json="{}",
            diagnostics_json="{}",
        )
        for trial, (value, status) in enumerate(
            ((1.0, "finite"), (3.0, "finite"), (None, "undefined"), (None, "infinite"))
        )
    ]
    summary = summarize(rows)[0]
    assert (summary.n_total, summary.n_finite, summary.n_undefined, summary.n_infinite) == (
        4,
        2,
        1,
        1,
    )
    assert summary.finite_mean == 2
    assert summary.finite_sample_sd == pytest.approx(math.sqrt(2))


@pytest.mark.parametrize(
    "update",
    [
        {"replicates": 1},
        {"mixing_probabilities": [1.1]},
        {"radii": [0]},
        {"shapes": [[2, 2]]},
        {"controls": ["constant", "constant"]},
        {"max_input_elements": 1},
        {"symbol_range": [2, 1]},
    ],
)
def test_invalid_study_design_fails(study_plan: StudyPlan, update: dict[str, JsonValue]) -> None:
    with pytest.raises((ParameterError, ValidationError)):
        StudyPlan.model_validate(study_plan.model_dump() | update)
